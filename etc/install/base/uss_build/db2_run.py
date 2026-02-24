#!/usr/bin/env python3
"""
DB2 SQL Runner Script
Loads build.conf, performs variable substitution in SQL files, and runs them using db2cmd/db2admin
Copyright IBM Corp. 2023, 2025
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Optional
import re
import tempfile

# Import batchtsocmd for DB2 operations
try:
    from batchtsocmd.main import db2cmd, db2admin
    from batchtsocmd import tsocmd
except ImportError:
    print("ERROR: batchtsocmd package not found. Install with: pip install batchtsocmd>=0.1.13")
    sys.exit(1)

# Import cbsa_utils for configuration loading
try:
    from cbsa_utils import BuildConfig
except ImportError:
    print("ERROR: cbsa_utils module not found. Ensure it's in the same directory.")
    sys.exit(1)


class DB2Runner:
    """Run DB2 SQL with variable substitution"""
    
    def __init__(self, config: BuildConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.substitution_vars = self._build_substitution_vars()
    
    def _build_substitution_vars(self) -> Dict[str, str]:
        """Build dictionary of variables for substitution
        
        Validates that required variables are specified in build.conf.
        Variables with defaults: DB2_HLQ, BANK_USER, and all CBSA_* variables
        DB2_OWNER defaults to $USER if available, otherwise must be specified
        Required variables (no defaults): DB2_SYSTEM, DSN_HLQ, DB2_TOOLLIB, DB2_DBRMLIB, DB2_VCAT
        """
        # Required variables that MUST be in build.conf (no defaults)
        required_vars = ['DB2_SYSTEM', 'DSN_HLQ', 'DB2_TOOLLIB', 'DB2_DBRMLIB', 'DB2_VCAT']
        
        # Check for missing required variables
        missing_vars = []
        for var in required_vars:
            if not self.config.get(var):
                missing_vars.append(var)
        
        # Check DB2_OWNER - must be in config or available from $USER
        db2_owner = self.config.get('DB2_OWNER')
        if not db2_owner:
            db2_owner = os.environ.get('USER')
            if not db2_owner:
                missing_vars.append('DB2_OWNER')
        
        # If any required variables are missing, report all of them and exit
        if missing_vars:
            print("ERROR: The following required variables are not specified in build.conf:")
            for var in missing_vars:
                if var == 'DB2_OWNER':
                    print(f"  - {var} (not in build.conf and $USER environment variable not set)")
                else:
                    print(f"  - {var}")
            print("\nPlease add these variables to your build.conf file.")
            sys.exit(1)
        
        # Build variables dictionary with defaults for optional variables
        # Ordered: DB2 variables first, then CBSA variables, then other variables
        vars_dict = {
            # DB2 Configuration
            'DB2_HLQ': self.config.get('DB2_HLQ', 'DB2V13'),
            'DB2_SYSTEM': self.config.get('DB2_SYSTEM'),
            'DSN_HLQ': self.config.get('DSN_HLQ'),
            'DB2_OWNER': db2_owner,
            'DB2_TOOLLIB': self.config.get('DB2_TOOLLIB'),
            'DB2_DBRMLIB': self.config.get('DB2_DBRMLIB'),
            'DB2_VCAT': self.config.get('DB2_VCAT'),
            'DB2_PLAN': self.config.get('DB2_DSNTEP_PLAN', 'DSNTEP13'),
            'DB2_DSNTEP_PLAN': self.config.get('DB2_DSNTEP_PLAN', 'DSNTEP13'),
            'DB2_DSNTIAD_PLAN': self.config.get('DB2_DSNTIAD_PLAN', 'DSNTIAD'),
            # CBSA Configuration
            'CBSA_DB': self.config.get('CBSA_DB', 'CBSADB'),
            'CBSA_PLAN': self.config.get('CBSA_PLAN', 'CBSAPLAN'),
            'CBSA_PACKAGE': self.config.get('CBSA_PACKAGE', 'CBSAPKG'),
            'CBSA_ACCOUNT_STOGROUP': self.config.get('CBSA_ACCOUNT_STOGROUP', 'CBSABASG'),
            'CBSA_CONTROL_STOGROUP': self.config.get('CBSA_CONTROL_STOGROUP', 'CBSACTSG'),
            'CBSA_PROCTRAN_STOGROUP': self.config.get('CBSA_PROCTRAN_STOGROUP', 'CBSAPTSG'),
            # Other Configuration
            'BANK_USER': self.config.get('BANK_USER', 'CICSUSER'),
        }
        
        if self.verbose:
            print("Substitution variables:")
            for key, value in sorted(vars_dict.items()):
                print(f"  {key}={value}")
        
        return vars_dict
    
    def substitute_sql(self, sql_content: str) -> str:
        """Perform variable substitution in SQL content
        
        Replaces ${VAR_NAME} with values from substitution_vars
        """
        def replace_var(match):
            var_name = match.group(1)
            if var_name in self.substitution_vars:
                return self.substitution_vars[var_name]
            else:
                print(f"WARNING: Variable ${{{var_name}}} not found in configuration")
                return match.group(0)
        
        # Replace ${VAR} patterns
        pattern = re.compile(r'\$\{([^}]+)\}')
        return pattern.sub(replace_var, sql_content)
    
    def run_sql_file(self, sql_file: Path, use_dsntiad: bool = False) -> bool:
        """Run SQL file with variable substitution
        
        Args:
            sql_file: Path to SQL file
            use_dsntiad: If True, use DB2_DSNTIAD_PLAN instead of DB2_DSNTEP_PLAN
            
        Returns:
            True if successful, False otherwise
        """
        if not sql_file.exists():
            print(f"ERROR: SQL file not found: {sql_file}")
            return False
        
        # Read SQL file
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Perform variable substitution
        substituted_sql = self.substitute_sql(sql_content)
        
        if self.verbose:
            print(f"\nRunning SQL from: {sql_file}")
            print("=" * 60)
            print(substituted_sql)
            print("=" * 60)
        
        # Get DB2 configuration
        db2_system = self.substitution_vars['DB2_SYSTEM']
        # Use DSNTIAD plan for grant operations, DSNTEP for regular SQL
        db2_plan = self.substitution_vars['DB2_DSNTIAD_PLAN'] if use_dsntiad else self.substitution_vars['DB2_DSNTEP_PLAN']
        db2_toollib = self.substitution_vars['DB2_TOOLLIB']
        dbrmlib = self.substitution_vars['DB2_DBRMLIB']
        db2_hlq = self.substitution_vars['DB2_HLQ']
        steplib = f"{db2_hlq}.SDSNLOAD"
        
        # Generate temporary file paths for SYSTSPRT and SYSPRINT output
        # Use absolute paths in /tmp directory
        import time
        timestamp = str(int(time.time() * 1000))
        systsprt_file = f"/tmp/db2_{timestamp}.systsprt"
        sysprint_file = f"/tmp/db2_{timestamp}.sysprint"
        
        if self.verbose:
            print(f"Output files:")
            print(f"  SYSTSPRT: {systsprt_file}")
            print(f"  SYSPRINT: {sysprint_file}")
        
        try:
            
            # For DSNTIAD operations (grants), use db2admin
            # For DSNTEP operations (regular SQL), use db2cmd
            if use_dsntiad:
                # Run using db2admin for DSNTIAD operations (grants)
                # Note: db2admin does not support dbrmlib parameter
                rc = db2admin(
                    sysin_content=substituted_sql,
                    system=db2_system,
                    plan=db2_plan,
                    toollib=db2_toollib,
                    steplib=steplib,
                    systsprt_file=systsprt_file,
                    sysprint_file=sysprint_file,
                    verbose=self.verbose
                )
            else:
                # Run using db2cmd for DSNTEP2 operations
                # db2cmd takes sysin_content and returns an integer return code
                if self.verbose:
                    print(f"\nCalling db2cmd with:")
                    print(f"  system={db2_system}")
                    print(f"  plan={db2_plan}")
                    print(f"  toollib={db2_toollib}")
                    print(f"  steplib={steplib}")
                    print(f"  dbrmlib={dbrmlib if dbrmlib else 'None'}")
                    print(f"  systsprt_file={systsprt_file}")
                    print(f"  sysprint_file={sysprint_file}")
                    print(f"  sysin_content length={len(substituted_sql)} bytes")
                
                if dbrmlib:
                    rc = db2cmd(
                        sysin_content=substituted_sql,
                        system=db2_system,
                        plan=db2_plan,
                        toollib=db2_toollib,
                        steplib=steplib,
                        dbrmlib=dbrmlib,
                        systsprt_file=systsprt_file,
                        sysprint_file=sysprint_file,
                        verbose=self.verbose
                    )
                else:
                    rc = db2cmd(
                        sysin_content=substituted_sql,
                        system=db2_system,
                        plan=db2_plan,
                        toollib=db2_toollib,
                        steplib=steplib,
                        systsprt_file=systsprt_file,
                        sysprint_file=sysprint_file,
                        verbose=self.verbose
                    )
            
            if self.verbose:
                print(f"\nReturn code: {rc}")
            
            if rc != 0:
                print(f"ERROR: SQL run failed with RC={rc}", file=sys.stderr)
                
                # Print SYSTSPRT output
                try:
                    # Files are tagged as IBM-1047 (EBCDIC), need to read with proper encoding
                    if os.path.exists(systsprt_file) and os.path.getsize(systsprt_file) > 0:
                        with open(systsprt_file, 'r', encoding='ibm1047') as f:
                            systsprt_content = f.read()
                        if systsprt_content.strip():
                            print("\n=== SYSTSPRT Output ===", file=sys.stderr)
                            print(systsprt_content, file=sys.stderr)
                    else:
                        print(f"\nWARNING: SYSTSPRT file is empty or does not exist: {systsprt_file}", file=sys.stderr)
                except Exception as e:
                    print(f"\nWARNING: Could not read SYSTSPRT file: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                
                # Print SYSPRINT output
                try:
                    # Files are tagged as IBM-1047 (EBCDIC), need to read with proper encoding
                    if os.path.exists(sysprint_file) and os.path.getsize(sysprint_file) > 0:
                        with open(sysprint_file, 'r', encoding='ibm1047') as f:
                            sysprint_content = f.read()
                        if sysprint_content.strip():
                            print("\n=== SYSPRINT Output ===", file=sys.stderr)
                            print(sysprint_content, file=sys.stderr)
                    else:
                        print(f"\nWARNING: SYSPRINT file is empty or does not exist: {sysprint_file}", file=sys.stderr)
                except Exception as e:
                    print(f"\nWARNING: Could not read SYSPRINT file: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                
                # Preserve temporary files for debugging
                print(f"\nTemporary files preserved for debugging:", file=sys.stderr)
                print(f"  SYSTSPRT: {systsprt_file}", file=sys.stderr)
                print(f"  SYSPRINT: {sysprint_file}", file=sys.stderr)
                
                return False
            
            # Clean up temporary files on success
            try:
                if os.path.exists(systsprt_file):
                    os.unlink(systsprt_file)
            except Exception:
                pass
            try:
                if os.path.exists(sysprint_file):
                    os.unlink(sysprint_file)
            except Exception:
                pass
            
            return True
            
        except Exception as e:
            print(f"ERROR: Exception during SQL run: {e}", file=sys.stderr)
            if self.verbose:
                import traceback
                traceback.print_exc()
            
            # Preserve temporary files for debugging on exception
            print(f"\nTemporary files preserved for debugging:", file=sys.stderr)
            print(f"  SYSTSPRT: {systsprt_file}", file=sys.stderr)
            print(f"  SYSPRINT: {sysprint_file}", file=sys.stderr)
            
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run DB2 SQL files with variable substitution from build.conf'
    )
    parser.add_argument(
        'sql_file',
        help='SQL file to execute (relative to script directory or absolute path)'
    )
    parser.add_argument(
        '--config',
        default='build.conf',
        help='Configuration file (default: build.conf)'
    )
    parser.add_argument(
        '--use-dsntiad',
        action='store_true',
        help='Use DB2_DSNTIAD_PLAN with db2admin instead of DB2_DSNTEP_PLAN with db2cmd (for grant operations)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = script_dir / config_path
    
    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        return 1
    
    try:
        config = BuildConfig(str(config_path))
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        return 1
    
    # Resolve SQL file path
    sql_file = Path(args.sql_file)
    if not sql_file.is_absolute():
        sql_file = script_dir / sql_file
    
    # Create runner and run
    runner = DB2Runner(config, verbose=args.verbose)
    
    # Run SQL
    success = runner.run_sql_file(sql_file, use_dsntiad=args.use_dsntiad)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
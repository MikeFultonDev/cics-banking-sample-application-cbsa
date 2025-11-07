#!/usr/bin/env python3
"""
CBSA Build Utilities
Common functions for CBSA USS-based build system
"""

import os
import sys
import subprocess
import re
from typing import Dict, List, Optional, Tuple


class BuildConfig:
    """Load and manage build configuration"""
    
    def __init__(self, config_file: str = "build.conf"):
        self.config = {}
        self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """Load configuration from file"""
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Expand variables in value
                        value = self._expand_vars(value)
                        self.config[key] = value
    
    def _expand_vars(self, value: str) -> str:
        """Expand ${VAR} references in configuration values"""
        pattern = re.compile(r'\$\{([^}]+)\}')
        
        def replace_var(match):
            var_name = match.group(1)
            if var_name in self.config:
                return self.config[var_name]
            elif var_name in os.environ:
                return os.environ[var_name]
            else:
                return match.group(0)
        
        # Keep expanding until no more variables found
        prev_value = None
        while prev_value != value:
            prev_value = value
            value = pattern.sub(replace_var, value)
        
        return value
    
    def get(self, key: str, default: str = "") -> str:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def __getitem__(self, key: str) -> str:
        """Allow dict-like access"""
        return self.config[key]


class MVSCommand:
    """Execute MVS commands via TSO"""
    
    @staticmethod
    def run_tso(command: str, verbose: bool = False) -> Tuple[int, str, str]:
        """Execute a TSO command"""
        if verbose:
            print(f"Executing TSO: {command}")
        
        try:
            result = subprocess.run(
                ['tsocmd', command],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if verbose:
                if result.stdout:
                    print(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    print(f"STDERR:\n{result.stderr}")
            
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except FileNotFoundError:
            return 1, "", "tsocmd not found - ensure you're running in USS environment"
        except Exception as e:
            return 1, "", str(e)
    
    @staticmethod
    def allocate_dataset(dsname: str, params: Dict[str, str], verbose: bool = False) -> bool:
        """Allocate a dataset using IDCAMS"""
        # Build DEFINE command
        define_cmd = f"DEFINE CLUSTER(NAME({dsname})"
        
        for key, value in params.items():
            define_cmd += f" {key}({value})"
        
        define_cmd += ")"
        
        # Create IDCAMS control cards
        control_cards = f"""
  DELETE {dsname}
  SET MAXCC=0
  {define_cmd}
"""
        
        # Write to temporary file
        temp_file = f"/tmp/idcams_{os.getpid()}.txt"
        try:
            with open(temp_file, 'w') as f:
                f.write(control_cards)
            
            # Execute IDCAMS
            cmd = f"IDCAMS <{temp_file}"
            rc, stdout, stderr = MVSCommand.run_tso(cmd, verbose)
            
            return rc == 0
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    @staticmethod
    def allocate_pds(dsname: str, recfm: str = "FB", lrecl: int = 80, 
                     blksize: int = 27920, space: str = "CYL(10,5,20)", 
                     verbose: bool = False) -> bool:
        """Allocate a PDS/PDSE"""
        cmd = f"ALLOCATE DATASET('{dsname}') NEW CATALOG DSORG(PO) RECFM({recfm}) LRECL({lrecl}) BLKSIZE({blksize}) SPACE({space}) DSNTYPE(LIBRARY)"
        
        if verbose:
            print(f"Allocating PDS: {dsname}")
        
        rc, stdout, stderr = MVSCommand.run_tso(cmd, verbose)
        return rc == 0
    
    @staticmethod
    def copy_member(source_file: str, target_ds: str, member: str, verbose: bool = False) -> bool:
        """Copy a USS file to a PDS member"""
        if verbose:
            print(f"Copying {source_file} to {target_ds}({member})")
        
        try:
            # Use cp command with MVS dataset syntax
            cmd = ['cp', '-F', 'record', source_file, f"//'{ target_ds}({member})'"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if verbose and result.returncode != 0:
                print(f"Copy failed: {result.stderr}")
            
            return result.returncode == 0
        except Exception as e:
            if verbose:
                print(f"Copy error: {e}")
            return False


class CobolCompiler:
    """COBOL compilation utilities"""
    
    def __init__(self, config: BuildConfig):
        self.config = config
    
    def compile_program(self, program: str, source_ds: str, output_ds: str, 
                       copylib_ds: str, dbrm_ds: Optional[str] = None,
                       verbose: bool = False) -> bool:
        """Compile a COBOL program"""
        if verbose:
            print(f"Compiling COBOL program: {program}")
        
        # Build compiler options
        options = [
            "CICS",
            "SQL",
            f"LIB('{copylib_ds}')",
            "NODYNAM",
            "RENT",
            "APOST",
            "OPTIMIZE(FULL)",
            "TRUNC(OPT)"
        ]
        
        if dbrm_ds:
            options.append(f"DBRMLIB('{dbrm_ds}')")
        
        # Create compile JCL
        compile_jcl = self._create_compile_jcl(program, source_ds, output_ds, options)
        
        # Submit JCL
        return self._submit_jcl(compile_jcl, verbose)
    
    def _create_compile_jcl(self, program: str, source_ds: str, 
                           output_ds: str, options: List[str]) -> str:
        """Create JCL for COBOL compilation"""
        cobol_hlq = self.config.get('COBOL_HLQ')
        cics_hlq = self.config.get('CICS_HLQ')
        db2_hlq = self.config.get('DB2_HLQ')
        le_hlq = self.config.get('LE_HLQ')
        
        jcl = f"""//COMPILE JOB ,CLASS=A,MSGCLASS=X,NOTIFY=&SYSUID
//COMPILE EXEC PGM=IGYCRCTL,REGION=0M
//STEPLIB  DD DISP=SHR,DSN={cobol_hlq}.SIGYCOMP
//         DD DISP=SHR,DSN={cics_hlq}.SDFHLOAD
//         DD DISP=SHR,DSN={db2_hlq}.SDSNLOAD
//SYSLIB   DD DISP=SHR,DSN={source_ds}
//         DD DISP=SHR,DSN={cics_hlq}.SDFHCOB
//         DD DISP=SHR,DSN={db2_hlq}.SDSNMACS
//SYSLIN   DD DISP=(NEW,PASS),UNIT=SYSDA,SPACE=(TRK,(10,10))
//SYSPRINT DD SYSOUT=*
//SYSUT1   DD UNIT=SYSDA,SPACE=(CYL,(1,1))
//SYSUT2   DD UNIT=SYSDA,SPACE=(CYL,(1,1))
//SYSUT3   DD UNIT=SYSDA,SPACE=(CYL,(1,1))
//SYSUT4   DD UNIT=SYSDA,SPACE=(CYL,(1,1))
//SYSUT5   DD UNIT=SYSDA,SPACE=(CYL,(1,1))
//SYSUT6   DD UNIT=SYSDA,SPACE=(CYL,(1,1))
//SYSUT7   DD UNIT=SYSDA,SPACE=(CYL,(1,1))
//SYSIN    DD DISP=SHR,DSN={source_ds}({program})
//SYSPARM  DD *
{' '.join(options)}
/*
"""
        return jcl
    
    def _submit_jcl(self, jcl: str, verbose: bool = False) -> bool:
        """Submit JCL and wait for completion"""
        temp_jcl = f"/tmp/compile_{os.getpid()}.jcl"
        try:
            with open(temp_jcl, 'w') as f:
                f.write(jcl)
            
            # Submit via submit command
            cmd = f"submit {temp_jcl}"
            rc, stdout, stderr = MVSCommand.run_tso(cmd, verbose)
            
            if verbose:
                print(f"JCL submission RC: {rc}")
            
            return rc == 0
        finally:
            if os.path.exists(temp_jcl):
                os.remove(temp_jcl)


class DB2Utilities:
    """DB2 utilities"""
    
    def __init__(self, config: BuildConfig):
        self.config = config
    
    def execute_sql(self, sql: str, verbose: bool = False) -> bool:
        """Execute SQL statements via DB2"""
        if verbose:
            print(f"Executing SQL:\n{sql}")
        
        db2_subsystem = self.config.get('DB2_SUBSYSTEM')
        db2_hlq = self.config.get('DB2_HLQ')
        dsntep_plan = self.config.get('DB2_DSNTEP_PLAN')
        dsntep_lib = self.config.get('DB2_DSNTEP_LOADLIB')
        
        # Create temporary SQL file
        temp_sql = f"/tmp/sql_{os.getpid()}.sql"
        temp_tso = f"/tmp/tso_{os.getpid()}.txt"
        
        try:
            with open(temp_sql, 'w') as f:
                f.write(sql)
            
            # Execute via DSNTEP2
            tso_cmd = f"""
DSN SYSTEM({db2_subsystem})
RUN PROGRAM(DSNTEP2) PLAN({dsntep_plan}) LIB('{dsntep_lib}')
END
"""
            
            with open(temp_tso, 'w') as f:
                f.write(tso_cmd)
            
            # This is a simplified version - actual implementation would need
            # proper JCL submission with SYSIN pointing to SQL file
            rc, stdout, stderr = MVSCommand.run_tso(f"IKJEFT01 <{temp_tso}", verbose)
            
            return rc == 0
        finally:
            for f in [temp_sql, temp_tso]:
                if os.path.exists(f):
                    os.remove(f)


def print_banner(message: str):
    """Print a formatted banner message"""
    width = len(message) + 4
    print("\n" + "=" * width)
    print(f"  {message}")
    print("=" * width + "\n")


def print_step(step_num: int, message: str):
    """Print a step message"""
    print(f"\n[Step {step_num}] {message}")
    print("-" * (len(message) + 10))


def check_prerequisites() -> bool:
    """Check if running in proper USS environment"""
    # Check for TSO command availability
    try:
        result = subprocess.run(['which', 'tsocmd'], capture_output=True)
        if result.returncode != 0:
            print("ERROR: tsocmd not found. Ensure you're running in z/OS USS environment.")
            return False
    except Exception:
        print("ERROR: Unable to check for tsocmd. Ensure you're running in z/OS USS environment.")
        return False
    
    return True

# Made with Bob

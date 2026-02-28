#!/usr/bin/env python3
"""
CBSA Build Utilities
Common functions for CBSA USS-based build system
Refactored to use Z Open Automation Utilities (ZOAU) Python interfaces
"""

import os
import sys
import re
import subprocess
from typing import Dict, List, Optional, Tuple

# Import ZOAU modules
from zoautil_py import datasets, mvscmd
from zoautil_py.ztypes import ZOAUResponse, DDStatement, DatasetDefinition, FileDefinition
from zoautil_py.exceptions import (
    DatasetCreateException,
    DatasetWriteException,
    ZOAUException
)

# Import db2sql, db2op, and tsocmd for DB2 and TSO operations
from batchtsocmd import db2sql, db2op, tsocmd

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
    """Execute MVS commands using batchtsocmd"""
    
    @staticmethod
    def run_tso(command: str, verbose: bool = False) -> Tuple[int, str, str]:
        """Execute a TSO command using batchtsocmd tsocmd API"""
        if verbose:
            print(f"Executing TSO: {command}")
        
        try:
            # Use batchtsocmd tsocmd API to execute TSO commands
            # The tsocmd function handles all the complexity of:
            # - Setting up SYSTSIN with the TSO command
            # - Configuring DD statements
            # - Executing via IKJEFT01
            # - Returning results
            result = tsocmd(
                command=command,
                verbose=verbose
            )
            
            if verbose:
                print(f"Return code: {result.rc}")
                if hasattr(result, 'output') and result.output:
                    print(f"Output:\n{result.output}")
                if hasattr(result, 'error') and result.error:
                    print(f"Error:\n{result.error}")
            
            # Return tuple of (rc, stdout, stderr) for compatibility
            stdout = result.output if hasattr(result, 'output') else ""
            stderr = result.error if hasattr(result, 'error') else ""
            return result.rc, stdout, stderr
            
        except Exception as e:
            if verbose:
                print(f"Error executing TSO command: {e}")
            return 1, "", str(e)
    
    @staticmethod
    def allocate_dataset(dsname: str, params: Dict[str, str], verbose: bool = False) -> bool:
        """Allocate a dataset using ZOAU datasets.create"""
        if verbose:
            print(f"Allocating dataset: {dsname}")
        
        try:
            # Delete if exists
            if datasets.exists(dsname):
                datasets.delete(dsname, verbose=verbose)
            
            # Map parameters to ZOAU create parameters
            dataset_type = params.get('TYPE', 'SEQ')
            
            # Build kwargs for ZOAU create
            create_kwargs = {
                'verbose': verbose
            }
            
            # Map common parameters
            if 'RECFM' in params:
                create_kwargs['record_format'] = params['RECFM']
            if 'LRECL' in params:
                create_kwargs['record_length'] = int(params['LRECL'])
            if 'BLKSIZE' in params:
                create_kwargs['block_size'] = int(params['BLKSIZE'])
            if 'SPACE' in params:
                # Parse space parameter (e.g., "CYL(10,5)")
                space_match = re.match(r'(\w+)\((\d+),(\d+)\)', params['SPACE'])
                if space_match:
                    unit, primary, secondary = space_match.groups()
                    create_kwargs['space_primary'] = int(primary)
                    create_kwargs['space_secondary'] = int(secondary)
                    create_kwargs['space_type'] = unit.lower()
            if 'VOLUMES' in params:
                create_kwargs['volumes'] = params['VOLUMES']
            
            # Create the dataset
            datasets.create(dsname, dataset_type, **create_kwargs)
            
            if verbose:
                print(f"Dataset {dsname} allocated successfully")
            
            return True
        except DatasetCreateException as e:
            if verbose:
                print(f"Failed to allocate dataset: {e}")
            return False
        except Exception as e:
            if verbose:
                print(f"Error allocating dataset: {e}")
            return False
    
    @staticmethod
    def allocate_pds(dsname: str, recfm: str = "FB", lrecl: int = 80, 
                     blksize: int = 27920, space: str = "CYL(10,5,20)", 
                     verbose: bool = False) -> bool:
        """Allocate a PDS/PDSE using ZOAU"""
        if verbose:
            print(f"Allocating PDS: {dsname}")
        
        try:
            # Delete if exists
            if datasets.exists(dsname):
                datasets.delete(dsname, verbose=verbose)
            
            # Parse space parameter
            space_match = re.match(r'(\w+)\((\d+),(\d+)(?:,(\d+))?\)', space)
            if not space_match:
                if verbose:
                    print(f"Invalid space parameter: {space}")
                return False
            
            unit, primary, secondary, directory = space_match.groups()
            
            # Create PDS using ZOAU
            datasets.create(
                dsname,
                'PDSE',  # Use PDSE (modern PDS)
                record_format=recfm,
                record_length=lrecl,
                block_size=blksize,
                space_primary=int(primary),
                space_secondary=int(secondary),
                space_type=unit.lower(),
                directory_blocks=int(directory) if directory else 20,
                verbose=verbose
            )
            
            if verbose:
                print(f"PDS {dsname} allocated successfully")
            
            return True
        except DatasetCreateException as e:
            if verbose:
                print(f"Failed to allocate PDS: {e}")
            return False
        except Exception as e:
            if verbose:
                print(f"Error allocating PDS: {e}")
            return False


class DB2Utilities:
    """DB2 utilities using batchtsocmd db2cmd/db2admin API"""
    
    def __init__(self, config: BuildConfig):
        self.config = config
    
    def execute_sql(self, sql: str, verbose: bool = False) -> bool:
        """Execute SQL statements via DB2 using batchtsocmd db2sql
        
        Note: Uses DSNTEP2 for SQL execution (DDL, DML, DQL, GRANT).
        For Db2 operator commands (-DISPLAY, -START, -STOP), use db2op with DSNTIAD instead.
        """
        if verbose:
            print(f"Executing SQL:\n{sql}")
        
        db2_subsystem = self.config.get('DB2_SYSTEM')
        db2_hlq = self.config.get('DB2_HLQ')
        dsntep_plan = self.config.get('DB2_PLAN', 'DSNTEP2')
        dsntep_lib = self.config.get('DB2_TOOLLIB', f'{db2_hlq}.RUNLIB.LOAD')
        
        try:
            # Execute DB2 SQL using batchtsocmd db2sql API
            # db2sql handles DDL, DML, DQL, and GRANT via DSNTEP2
            # For Db2 operator commands, use db2op instead
            rc = db2sql(
                sysin_content=sql,
                system=db2_subsystem,
                plan=dsntep_plan,
                toollib=dsntep_lib,
                verbose=verbose
            )
            
            if verbose:
                print(f"Return code: {rc}")
            
            # Check return code (0 = success)
            return rc == 0
            
        except Exception as e:
            if verbose:
                print(f"Error executing SQL: {e}")
            return False


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
    """Check if ZOAU is available"""
    try:
        # Try to import ZOAU modules
        import zoautil_py
        
        # Try a simple ZOAU operation
        hlq = datasets.get_hlq()
        
        print(f"ZOAU is available. Current HLQ: {hlq}")
        return True
    except ImportError:
        print("ERROR: ZOAU Python modules not found. Ensure ZOAU is installed and PYTHONPATH is set correctly.")
        return False
    except Exception as e:
        print(f"ERROR: ZOAU check failed: {e}")
        return False

# Made with Bob

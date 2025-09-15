#!/usr/bin/env python3
"""
Quick script to run the migration to convert ENUMs to VARCHAR
"""
import subprocess
import sys
import os

def run_migration():
    try:
        # Change to backend directory
        os.chdir('backend')
        
        # Run the alembic upgrade
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration completed successfully!")
            print(result.stdout)
        else:
            print("❌ Migration failed:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Debug script to check the actual enum values in the database
"""
import asyncpg
import asyncio
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/autoscaling_db")

async def check_enum_values():
    try:
        # Parse the DATABASE_URL to extract connection parameters
        import urllib.parse
        parsed = urllib.parse.urlparse(DATABASE_URL)
        
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/')
        )
        
        print("=== Checking enum types in database ===")
        
        # Check what enum types exist
        enum_query = """
        SELECT t.typname, e.enumlabel, e.enumsortorder
        FROM pg_type t 
        JOIN pg_enum e ON t.oid = e.enumtypid  
        WHERE t.typname IN ('userrole', 'authprovider')
        ORDER BY t.typname, e.enumsortorder;
        """
        
        results = await conn.fetch(enum_query)
        
        if not results:
            print("❌ No userrole or authprovider enums found!")
        else:
            current_enum = None
            for row in results:
                if row['typname'] != current_enum:
                    print(f"\n📋 Enum: {row['typname']}")
                    current_enum = row['typname']
                print(f"  - {row['enumlabel']}")
        
        # Check current user data
        print("\n=== Current user data ===")
        user_query = "SELECT id, email, role, auth_provider FROM users LIMIT 5;"
        user_results = await conn.fetch(user_query)
        
        if not user_results:
            print("No users found")
        else:
            for user in user_results:
                print(f"User {user['id']}: {user['email']} - role: '{user['role']}', auth_provider: '{user['auth_provider']}'")
        
        # Check alembic version
        print("\n=== Alembic version ===")
        version_query = "SELECT version_num FROM alembic_version;"
        version_result = await conn.fetchrow(version_query)
        if version_result:
            print(f"Current migration version: {version_result['version_num']}")
        else:
            print("No alembic version found")
            
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")

if __name__ == "__main__":
    asyncio.run(check_enum_values())
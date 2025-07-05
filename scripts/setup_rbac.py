#!/usr/bin/env python3
"""
Setup script for RBAC system.
Run this after database migrations to populate default RBAC data.
"""

import sys
import os
import asyncio

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.scripts.seed_rbac_data import main

if __name__ == "__main__":
    print("Setting up RBAC system...")
    print("This will create default permissions, roles, and admin user.")
    
    try:
        asyncio.run(main())
        print("\n✅ RBAC setup completed successfully!")
        print("\nDefault admin user created:")
        print("  Email: admin@rental.com")
        print("  Password: admin123")
        print("  Please change the password after first login.")
        
    except Exception as e:
        print(f"\n❌ RBAC setup failed: {e}")
        sys.exit(1)
#!/usr/bin/env python
"""
Initialize MongoDB Atlas database and collections
Run this after deployment to ensure the database and collections exist
"""
import os
import sys
import time
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

def init_mongodb():
    try:
        mongo_uri = os.environ.get('MONGO_URI')
        print(f"[DEBUG] MONGO_URI set: {bool(mongo_uri)}")
        
        if not mongo_uri:
            print("❌ MONGO_URI environment variable not set!")
            sys.exit(1)
        
        # Mask password in logs
        masked_uri = mongo_uri.replace(mongo_uri.split('@')[0].split('//')[1], 'USER:PASS')
        print(f"[DEBUG] Connecting to: {masked_uri}")
        
        # Connect with timeout
        print("Attempting connection to MongoDB Atlas...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000)
        
        # Force connection attempt
        client.server_info()
        print("✓ Connected to MongoDB Atlas")
        
        db = client['mediasnap']
        print(f"✓ Using database: mediasnap")
        
        # List existing collections
        existing_collections = db.list_collection_names()
        print(f"[DEBUG] Existing collections: {existing_collections}")
        
        # Create collections if they don't exist
        if 'download_history' not in existing_collections:
            print("Creating 'download_history' collection...")
            db.create_collection('download_history')
            print("✓ Created 'download_history' collection")
        else:
            print("✓ 'download_history' collection already exists")
        
        # Create indexes for better query performance
        print("Creating indexes...")
        db['download_history'].create_index('created_at')
        db['download_history'].create_index('platform')
        db['download_history'].create_index('status')
        print("✓ Indexes created/verified")
        
        # Test the connection by inserting and deleting a test document
        print("Running connection test...")
        result = db['download_history'].insert_one({
            'test': True,
            'timestamp': None,
            'message': 'Connection test document - will be deleted'
        })
        print(f"✓ Test document inserted: {result.inserted_id}")
        
        db['download_history'].delete_one({'_id': result.inserted_id})
        print("✓ Test document deleted")
        
        # List final collections
        final_collections = db.list_collection_names()
        print(f"[DEBUG] Final collections in database: {final_collections}")
        
        # Get database stats
        stats = db.command('dbStats')
        print(f"[DEBUG] Database stats - Collections: {stats.get('collections')}, Size: {stats.get('dataSize')} bytes")
        
        print("\n✅ MongoDB Atlas initialization completed successfully!")
        client.close()
        return True
        
    except ServerSelectionTimeoutError as e:
        print(f"\n❌ Cannot reach MongoDB Atlas (connection timeout): {e}")
        print("Please verify:")
        print("  - MONGO_URI is correct")
        print("  - MongoDB Atlas cluster is running")
        print("  - Network access/IP whitelist is configured in Atlas")
        sys.exit(1)
    except OperationFailure as e:
        print(f"\n❌ MongoDB operation failed (auth error?): {e}")
        print("Please verify credentials in MONGO_URI")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ MongoDB initialization failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    init_mongodb()

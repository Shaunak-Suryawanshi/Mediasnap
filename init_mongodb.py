#!/usr/bin/env python
"""
Initialize MongoDB Atlas database and collections
Run this after deployment to ensure the database and collections exist
"""
import os
import sys
from pymongo import MongoClient

def init_mongodb():
    try:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb+srv://shaunak436:emmanuel123@cluster0.igrxhvt.mongodb.net/mediasnap?retryWrites=true&w=majority')
        
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client['mediasnap']
        
        # Create collections if they don't exist
        # MongoDB creates collection on first insert, but we'll create them explicitly
        if 'download_history' not in db.list_collection_names():
            db.create_collection('download_history')
            print("✓ Created 'download_history' collection")
        
        # Create indexes for better query performance
        db['download_history'].create_index('created_at')
        db['download_history'].create_index('platform')
        db['download_history'].create_index('status')
        print("✓ Created indexes on download_history")
        
        # Test the connection by inserting and deleting a test document
        result = db['download_history'].insert_one({
            'test': True,
            'timestamp': None
        })
        db['download_history'].delete_one({'_id': result.inserted_id})
        print("✓ Connection test successful")
        
        print("\n✅ MongoDB Atlas initialization completed!")
        client.close()
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB initialization failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_mongodb()

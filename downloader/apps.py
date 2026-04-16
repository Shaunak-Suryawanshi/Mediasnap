from django.apps import AppConfig


class DownloaderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'downloader'

    def ready(self):
        """Initialize MongoDB on app startup"""
        from pymongo import MongoClient
        import os
        
        try:
            mongo_uri = os.environ.get('MONGO_URI')
            if mongo_uri:
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                db = client['mediasnap']
                
                # Create collection if it doesn't exist
                if 'download_history' not in db.list_collection_names():
                    db.create_collection('download_history')
                    print("[INIT] Created MongoDB download_history collection")
                    
                    # Create indexes
                    db['download_history'].create_index('created_at')
                    db['download_history'].create_index('platform')
                    db['download_history'].create_index('status')
                    print("[INIT] Indexes created")
                
                client.close()
        except Exception as e:
            print(f"[WARN] MongoDB initialization failed: {e}")
            # Don't crash if MongoDB fails - app should still work
            pass

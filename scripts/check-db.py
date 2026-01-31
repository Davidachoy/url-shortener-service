#!/usr/bin/env python3
"""
Script to check database contents.
Usage: python scripts/check-db.py [--limit N]
"""
import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings


async def check_database(limit: int = 10):
    """Check database contents and display URL records."""
    print("=" * 80)
    print("DATABASE CHECK")
    print("=" * 80)
    print(f"Database URL: {settings.DATABASE_URL}")
    print()
    
    engine = create_async_engine(settings.DATABASE_URL)
    
    try:
        async with engine.connect() as conn:
            # Check connection
            print("✓ Database connection successful")
            print()
            
            # Get table info
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public'"
            ))
            tables = result.fetchall()
            print(f"Tables in database: {', '.join(t[0] for t in tables)}")
            print()
            
            # Get URL count
            result = await conn.execute(text("SELECT COUNT(*) FROM urls"))
            count = result.scalar()
            print(f"Total URLs in database: {count}")
            print()
            
            if count > 0:
                # Get recent URLs
                result = await conn.execute(text(
                    f"SELECT id, short_code, target_url, created_at "
                    f"FROM urls ORDER BY id DESC LIMIT :limit"
                ), {"limit": limit})
                rows = result.fetchall()
                
                print(f"Recent URLs (showing {len(rows)}):")
                print("-" * 80)
                for row in rows:
                    print(f"ID: {row[0]:<4} | Code: {row[1]:<10} | Created: {row[3]}")
                    print(f"         | URL: {row[2]}")
                    print()
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    finally:
        await engine.dispose()
    
    return True


async def check_redis():
    """Check Redis cache contents."""
    from redis.asyncio import Redis
    
    print("=" * 80)
    print("REDIS CACHE CHECK")
    print("=" * 80)
    print(f"Redis URL: {settings.REDIS_URL}")
    print()
    
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    try:
        # Test connection
        await redis_client.ping()
        print("✓ Redis connection successful")
        print()
        
        # Get all keys
        keys = await redis_client.keys('*')
        print(f"Total keys in cache: {len(keys)}")
        
        if keys:
            print()
            print("Cached URLs:")
            print("-" * 80)
            
            # Filter out clicks keys and test keys
            url_keys = [k for k in keys if not k.startswith('clicks:') and k != 'test_key']
            
            for key in url_keys[:10]:  # Show first 10
                value = await redis_client.get(key)
                ttl = await redis_client.ttl(key)
                ttl_str = f"{ttl}s" if ttl > 0 else "no expiry"
                print(f"Code: {key:<10} | URL: {value}")
                print(f"         | TTL: {ttl_str}")
                print()
        
        await redis_client.aclose()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Check database and cache contents')
    parser.add_argument('--limit', type=int, default=10,
                       help='Number of recent URLs to show (default: 10)')
    parser.add_argument('--db-only', action='store_true',
                       help='Check database only')
    parser.add_argument('--redis-only', action='store_true',
                       help='Check Redis cache only')
    
    args = parser.parse_args()
    
    success = True
    
    if not args.redis_only:
        success = await check_database(args.limit) and success
        print()
    
    if not args.db_only:
        success = await check_redis() and success
    
    if success:
        print("=" * 80)
        print("✓ All checks passed!")
        print("=" * 80)
    else:
        print("=" * 80)
        print("✗ Some checks failed")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

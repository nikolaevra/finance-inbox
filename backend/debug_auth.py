#!/usr/bin/env python3
"""Debug script to help diagnose JWT token issues"""

import os
import jwt
import json
from dotenv import load_dotenv

load_dotenv()

def debug_jwt_token():
    """Debug JWT token verification"""
    
    print("🔍 JWT Debug Information")
    print("=" * 50)
    
    # Check environment variables
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    print(f"📍 Supabase URL: {supabase_url}")
    print(f"🔑 JWT Secret exists: {'✅' if jwt_secret else '❌'}")
    print(f"🗝️  Supabase Key exists: {'✅' if supabase_key else '❌'}")
    
    if jwt_secret:
        print(f"🔐 JWT Secret length: {len(jwt_secret)} characters")
        print(f"🔐 JWT Secret starts with: {jwt_secret[:20]}...")
    
    print("\n" + "=" * 50)
    print("📝 Instructions:")
    print("1. Get a token from your frontend browser:")
    print("   - Open browser dev tools")
    print("   - Go to Application/Storage > Local Storage")
    print("   - Look for supabase session data")
    print("   - Copy the access_token value")
    print("2. Run this script with the token:")
    print("   python debug_auth.py <your_token_here>")
    
    # If token provided as argument
    import sys
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print(f"\n🔍 Analyzing token: {token[:50]}...")
        
        try:
            # Decode without verification first to see the payload
            unverified = jwt.decode(token, options={"verify_signature": False})
            print(f"\n📋 Token payload (unverified):")
            print(json.dumps(unverified, indent=2))
            
            # Check issuer
            iss = unverified.get('iss')
            aud = unverified.get('aud')
            exp = unverified.get('exp')
            
            print(f"\n🏢 Issuer (iss): {iss}")
            print(f"👥 Audience (aud): {aud}")
            print(f"⏰ Expires (exp): {exp}")
            
            # Try to verify with current secret
            if jwt_secret:
                try:
                    verified = jwt.decode(
                        token, 
                        jwt_secret, 
                        algorithms=["HS256"],
                        audience="authenticated"
                    )
                    print(f"\n✅ Token verification successful!")
                    print(f"👤 User ID: {verified.get('sub')}")
                    print(f"📧 Email: {verified.get('email')}")
                    
                except jwt.ExpiredSignatureError:
                    print(f"\n⏰ Token has expired")
                    
                except jwt.InvalidAudienceError:
                    print(f"\n👥 Invalid audience. Expected 'authenticated', got: {aud}")
                    
                except jwt.InvalidSignatureError:
                    print(f"\n❌ Invalid signature - JWT secret might be wrong")
                    print(f"💡 Make sure you're using the JWT secret from:")
                    print(f"   Supabase Dashboard > Settings > API > JWT Secret")
                    print(f"   NOT the anon key or service role key")
                    
                except Exception as e:
                    print(f"\n❌ Verification failed: {e}")
            
        except Exception as e:
            print(f"\n❌ Failed to decode token: {e}")

if __name__ == "__main__":
    debug_jwt_token() 
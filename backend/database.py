"""Supabase client configuration.

This module replaces the local PostgreSQL connection with a Supabase client.
The models remain the same but operations are performed through the Supabase
API using ``supabase-py``.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_db() -> Client:
    """Return a Supabase client instance."""
    return supabase

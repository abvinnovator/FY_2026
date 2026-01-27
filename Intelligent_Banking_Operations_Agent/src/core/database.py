from __future__ import annotations

import asyncio
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis

from .config import get_settings


_mongo_client: AsyncIOMotorClient | None = None
_mongo_db: AsyncIOMotorDatabase | None = None
_redis_client: Redis | None = None


async def get_mongo_client() -> AsyncIOMotorClient:
	"""Create or return a cached MongoDB client.

	This function is safe to call multiple times; it caches the client per process.
	"""
	global _mongo_client
	if _mongo_client is None:
		settings = get_settings()
		_mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
	return _mongo_client


async def get_database() -> AsyncIOMotorDatabase:
	"""Return a handle to the configured MongoDB database."""
	global _mongo_db
	if _mongo_db is None:
		client = await get_mongo_client()
		settings = get_settings()
		_mongo_db = client[settings.mongodb_db]
	return _mongo_db


async def get_redis_client() -> Redis:
	"""Create or return a cached Redis client."""
	global _redis_client
	if _redis_client is None:
		settings = get_settings()
		_redis_client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
	return _redis_client


async def close_connections() -> None:
	"""Close Mongo and Redis connections (for graceful shutdown)."""
	global _mongo_client, _redis_client, _mongo_db
	if _mongo_client is not None:
		_mongo_client.close()
		_mongo_client = None
		_mongo_db = None
	if _redis_client is not None:
		await _redis_client.close()
		_redis_client = None


async def ping() -> dict[str, Any]:
	"""Ping datastores for health checks."""
	db = await get_database()
	redis = await get_redis_client()
	# Basic operations to validate connectivity
	server_info = await db.command({"ping": 1})
	redis_ok = await redis.ping()
	return {"mongo": server_info, "redis": redis_ok}



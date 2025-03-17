from discord import Member, TextChannel, Embed, Permissions
from typing import Optional, List
import datetime
import asyncio
import discord

# Store muted users and their original roles
muted_users = {}

async def clear_messages(channel: TextChannel, limit: int = 100, user: Optional[Member] = None) -> int:
    """Clear messages from a channel, optionally filtered by user"""
    if user:
        # Delete messages from specific user
        def check(msg):
            return msg.author.id == user.id
            
        deleted = await channel.purge(limit=limit, check=check)
    else:
        # Delete all messages
        deleted = await channel.purge(limit=limit)
        
    return len(deleted)

async def mute_user(member: Member, minutes: int = 10, reason: str = "No reason provided") -> bool:
    """Mute a user for a specified time"""
    # Check if the bot has permission to manage roles
    if not member.guild.me.guild_permissions.manage_roles:
        return False
        
    # Look for mute role or create one
    mute_role = discord.utils.get(member.guild.roles, name="Muted")
    if not mute_role:
        try:
            # Create mute role with proper permissions
            mute_role = await member.guild.create_role(name="Muted", reason="Created for muting users")
            
            # Set permissions for all channels
            for channel in member.guild.channels:
                await channel.set_permissions(
                    mute_role,
                    send_messages=False,
                    add_reactions=False,
                    speak=False
                )
        except:
            return False
    
    try:
        # Store current roles
        muted_users[member.id] = [role for role in member.roles if role != member.guild.default_role]
        
        # Remove roles and add mute role
        await member.edit(roles=[mute_role], reason=reason)
        
        # Schedule unmute
        if minutes > 0:
            await asyncio.sleep(minutes * 60)
            await unmute_user(member)
            
        return True
    except:
        return False

async def unmute_user(member: Member) -> bool:
    """Unmute a previously muted user"""
    try:
        if member.id in muted_users:
            # Restore original roles
            await member.edit(roles=muted_users[member.id])
            del muted_users[member.id]
            return True
        else:
            # Just remove the mute role
            mute_role = discord.utils.get(member.guild.roles, name="Muted")
            if mute_role and mute_role in member.roles:
                await member.remove_roles(mute_role)
            return True
    except:
        return False

async def kick_user(member: Member, reason: str = "No reason provided") -> bool:
    """Kick a user from the server"""
    try:
        await member.kick(reason=reason)
        return True
    except:
        return False

async def ban_user(member: Member, delete_days: int = 1, reason: str = "No reason provided") -> bool:
    """Ban a user from the server"""
    try:
        await member.ban(delete_message_days=delete_days, reason=reason)
        return True
    except:
        return False

def create_mod_log(action: str, mod: Member, target: Member, reason: str) -> Embed:
    """Create a moderation log embed"""
    colors = {
        "mute": 0xf39c12,   # Orange
        "unmute": 0x2ecc71,  # Green
        "kick": 0xe74c3c,    # Red
        "ban": 0xc0392b,     # Dark Red
        "clear": 0x3498db,   # Blue
    }
    
    embed = Embed(
        title=f"Moderation Action: {action.title()}", 
        color=colors.get(action.lower(), 0x95a5a6),
        timestamp=datetime.datetime.now()
    )
    
    embed.add_field(name="Moderator", value=f"{mod.mention} ({mod.id})", inline=False)
    embed.add_field(name="Target User", value=f"{target.mention} ({target.id})", inline=False)
    embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
    
    return embed

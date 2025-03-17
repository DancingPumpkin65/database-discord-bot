from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os
import io
import aiohttp
import asyncio
from typing import Tuple, Optional

# Create directory for fonts and backgrounds if they don't exist
os.makedirs("assets/fonts", exist_ok=True)
os.makedirs("assets/backgrounds", exist_ok=True)

# Default font paths - you'll need to provide these fonts or use system fonts
FONT_REGULAR = "assets/fonts/Poppins-Regular.ttf"
FONT_BOLD = "assets/fonts/Poppins-Bold.ttf"

# Default colors using a nice color scheme
PRIMARY_COLOR = (114, 137, 218)  # Discord blurple
SECONDARY_COLOR = (255, 255, 255)  # White
ACCENT_COLOR = (46, 204, 113)  # Green accent
DARK_BG = (35, 39, 42)  # Discord dark
LIGHT_TEXT = (255, 255, 255)  # White text

# If the specified fonts don't exist, fall back to default system fonts
if not os.path.exists(FONT_REGULAR):
    FONT_REGULAR = None  # Will use default
if not os.path.exists(FONT_BOLD):
    FONT_BOLD = None  # Will use default

async def download_image(url: str) -> Optional[bytes]:
    """Download an image from a URL"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

async def create_welcome_card(
    username: str, 
    avatar_url: str, 
    server_name: str, 
    member_count: int, 
    background_url: Optional[str] = None,
    accent_color: Tuple[int, int, int] = ACCENT_COLOR,
    custom_message: Optional[str] = None
) -> Optional[io.BytesIO]:
    """Create a stylish welcome card for new members"""
    try:
        # Card dimensions (16:9 aspect ratio - looks good in Discord)
        width, height = 1200, 675
        
        # Create base image with dark background
        card = Image.new('RGBA', (width, height), DARK_BG)
        draw = ImageDraw.Draw(card)
        
        # Load custom background if provided
        if background_url:
            bg_data = await download_image(background_url)
            if bg_data:
                background = Image.open(io.BytesIO(bg_data)).convert("RGBA")
                # Resize and crop to fit our card dimensions
                bg_ratio = max(width / background.width, height / background.height)
                bg_width = int(background.width * bg_ratio)
                bg_height = int(background.height * bg_ratio)
                background = background.resize((bg_width, bg_height), Image.LANCZOS)
                
                # Center crop
                left = (bg_width - width) // 2
                top = (bg_height - height) // 2
                background = background.crop((left, top, left + width, top + height))
                
                # Apply slight blur and darken for better text visibility
                background = background.filter(ImageFilter.GaussianBlur(5))
                overlay = Image.new('RGBA', (width, height), (0, 0, 0, 110))  # Semi-transparent black
                background = Image.alpha_composite(background, overlay)
                
                # Use the background
                card = background
                draw = ImageDraw.Draw(card)
        
        # Add decorative elements
        # Top and bottom accent bars
        draw.rectangle([(0, 0), (width, 8)], fill=accent_color)  # Top bar
        draw.rectangle([(0, height-8), (width, height)], fill=accent_color)  # Bottom bar
        
        # Add a subtle gradient overlay
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)
        for y in range(height):
            # Create a gradient from top to bottom
            alpha = int(150 - (y / height * 80))  # Fade from visible to less visible
            gradient_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
        
        card = Image.alpha_composite(card, gradient)
        draw = ImageDraw.Draw(card)
        
        # Download and process avatar
        avatar_data = await download_image(avatar_url)
        if not avatar_data:
            # If avatar can't be downloaded, create a placeholder
            avatar = Image.new('RGBA', (256, 256), accent_color)
            avatar_draw = ImageDraw.Draw(avatar)
            avatar_draw.text((128, 128), username[0].upper(), fill=LIGHT_TEXT, anchor='mm',
                           font=ImageFont.truetype(FONT_BOLD, 100) if FONT_BOLD else ImageFont.load_default())
        else:
            avatar = Image.open(io.BytesIO(avatar_data)).convert("RGBA")
        
        # Resize avatar to desired size
        avatar_size = 180
        avatar = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)
        
        # Create circular mask for avatar
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        
        # Apply circular mask to avatar
        avatar_circle = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        avatar_circle.putalpha(mask)
        
        # Create a slightly larger circle for the avatar border
        border_size = avatar_size + 10
        avatar_border = Image.new('RGBA', (border_size, border_size), accent_color)
        border_mask = Image.new('L', (border_size, border_size), 0)
        border_draw = ImageDraw.Draw(border_mask)
        border_draw.ellipse((0, 0, border_size, border_size), fill=255)
        avatar_border.putalpha(border_mask)
        
        # Center the avatar on the border
        avatar_with_border = avatar_border.copy()
        avatar_with_border.paste(avatar_circle, (5, 5), avatar_circle)
        
        # Position for the avatar
        avatar_pos_x = (width - border_size) // 2
        avatar_pos_y = 120  # From top
        
        # Place avatar with border on card
        card.paste(avatar_with_border, (avatar_pos_x, avatar_pos_y), avatar_with_border)
        
        # Load fonts with fallbacks
        try:
            username_font = ImageFont.truetype(FONT_BOLD, 60) if FONT_BOLD else ImageFont.load_default()
            title_font = ImageFont.truetype(FONT_BOLD, 36) if FONT_BOLD else ImageFont.load_default()
            subtitle_font = ImageFont.truetype(FONT_REGULAR, 28) if FONT_REGULAR else ImageFont.load_default()
            small_font = ImageFont.truetype(FONT_REGULAR, 24) if FONT_REGULAR else ImageFont.load_default()
        except Exception as e:
            print(f"Error loading fonts: {e} - Using default fonts")
            username_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Calculate positions
        center_x = width // 2
        
        # Add welcome text
        welcome_y = avatar_pos_y + border_size + 30
        draw.text((center_x, welcome_y), "WELCOME", fill=LIGHT_TEXT, font=title_font, anchor="mt")
        
        # Add username (with proper text wrapping if too long)
        username_y = welcome_y + 50
        if len(username) > 20:
            username_font = ImageFont.truetype(FONT_BOLD, 40) if FONT_BOLD else ImageFont.load_default()
        draw.text((center_x, username_y), username, fill=LIGHT_TEXT, font=username_font, anchor="mt")
        
        # Add custom message or default message
        message = custom_message or f"Welcome to {server_name}!"
        message_y = username_y + 70
        draw.text((center_x, message_y), message, fill=LIGHT_TEXT, font=subtitle_font, anchor="mt")
        
        # Add member count with a nice label
        count_y = message_y + 60
        draw.text((center_x, count_y), f"You are the {member_count}{'th' if member_count % 10 != 1 else 'st'} member", 
                 fill=SECONDARY_COLOR, font=small_font, anchor="mt")
        
        # Add decorative element at bottom
        decoration_y = height - 50
        draw.text((center_x, decoration_y), "• • •", fill=accent_color, font=subtitle_font, anchor="mt")
        
        # Save to buffer
        buffer = io.BytesIO()
        card.save(buffer, format="PNG")
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        print(f"Error creating welcome card: {e}")
        return None

# Function to generate an embed alongside the welcome image
def create_welcome_embed(username, server_name, member_count, user_id):
    """Create a welcome embed to accompany the welcome card"""
    from discord import Embed
    
    embed = Embed(
        title=f"Welcome to {server_name}!",
        description=f"We're happy to have you here, {username}!",
        color=0x2ecc71
    )
    
    embed.set_footer(text=f"Member #{member_count} • ID: {user_id}")
    
    # Add some helpful information
    embed.add_field(name="Getting Started", value="Check out <#CHANNEL_ID> to get started!", inline=False)
    embed.add_field(name="Rules", value="Please read our rules in <#CHANNEL_ID>", inline=False)
    
    return embed

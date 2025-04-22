import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import urllib.parse
import json
import math
import os.path

# Load environment variables
load_dotenv()

# Get the directory containing the bot.py file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the project root
PROJECT_ROOT = os.path.dirname(BASE_DIR)
# Define the path to the data file
VENUES_FILE = os.path.join(PROJECT_ROOT, 'data', 'happyhourstlv_enriched.json')

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
CHOOSING_LANGUAGE, CHOOSING_ACTION, CHOOSING_LOCATION, CHOOSING_VIBE, WAITING_FOR_LOCATION = range(5)

# Translations dictionary
TRANSLATIONS = {
    'en': {
        'welcome': (
            "Welcome to Happy Hour TLV Bot! 🍻\n\n"
            "I'm your personal guide to the best drink deals in Tel Aviv!\n\n"
            "Here's what I can help you with:\n"
            "🔍 Find happy hours by location\n"
            "📍 Find venues near you\n"
            "⏰ See what's happening right now\n"
            "🌟 Check out popular spots\n"
            "ℹ️ Learn more about the bot\n\n"
            "What would you like to do?"
        ),
        'find_happy_hour': "🔍 Find Happy Hour",
        'find_nearby': "📍 Find Nearby",
        'current_happy_hours': "⏰ Current Happy Hours",
        'popular_places': "🌟 Popular Places",
        'about': "ℹ️ About",
        'choose_area': "📍 Choose an area in Tel Aviv to explore happy hours:",
        'share_location': "📍 Share your location to find nearby venues",
        'no_current_hours': "😔 No happy hours currently running!\n\nWould you like to see all available happy hours instead?",
        'current_hours_header': "🎉 Current happy hours (at {})",
        'popular_header': "🌟 Most Popular Happy Hours in Tel Aviv:",
        'area_header': "🎉 Happy Hours in {}:",
        'nearby_header': "📍 Venues near you:",
        'more_options': "\nWant to see more options? Use the buttons below!",
        'refresh': "🔄 Refresh",
        'new_search': "🔍 New Search",
        'main_menu': "🏠 Main Menu",
        'about_text': (
            "🍻 *Happy Hour TLV Bot*\n\n"
            "Your ultimate guide to the best drink deals in Tel Aviv!\n\n"
            "Features:\n"
            "• Real-time happy hour updates\n"
            "• Location-based search\n"
            "• Find venues near you\n"
            "• Detailed venue information\n"
            "• Price range indicators\n"
            "• Venue vibes and descriptions\n\n"
            "Use /start anytime to begin your search!\n\n"
            "Cheers! 🥂"
        ),
        'welcome_back': "Welcome back! What would you like to do?",
        'change_language': "🌐 Change Language",
        'locations': {
            "Dizengoff": "Dizengoff",
            "Florentin": "Florentin",
            "Rothschild": "Rothschild",
            "Carmel Market": "Carmel Market"
        },
        'error_loading_venues': "❌ Sorry, I couldn't load the venues at the moment. Please try again later.",
        'error_processing_location': "❌ Sorry, I had trouble processing your location. Please try again.",
        'no_nearby_venues': "😔 No venues found nearby. Try increasing the search radius or checking a different area.",
        'current_happy_hour': "🔥 Currently in Happy Hour!",
        'distance_away': "📍 {}km away",
        'choose_radius': "📍 Choose search radius:",
        'choose_vibe': "🌟 Choose a vibe to explore venues:",
        'no_vibe_venues': "😔 No venues found with that vibe. Try another one!",
        'vibe_header': "🌟 Venues with {} vibe:",
        'vibes': {
            "Chill": "Chill",
            "Trendy": "Trendy",
            "Upscale": "Upscale",
            "Casual": "Casual"
        },
    },
    'he': {
        'welcome': (
            "ברוכים הבאים לבוט Happy Hour TLV! 🍻\n\n"
            "אני המדריך האישי שלך למבצעי השתייה הטובים ביותר בתל אביב!\n\n"
            "הנה במה אני יכול לעזור:\n"
            "🔍 חיפוש הפי אוור לפי מיקום\n"
            "📍 מצא מקומות קרובים אליך\n"
            "⏰ ראה מה קורה עכשיו\n"
            "🌟 בדוק מקומות פופולריים\n"
            "ℹ️ מידע נוסף על הבוט\n\n"
            "מה תרצה לעשות?"
        ),
        'find_happy_hour': "🔍 חפש הפי אוור",
        'find_nearby': "📍 מצא קרוב",
        'current_happy_hours': "⏰ הפי אוור עכשיו",
        'popular_places': "🌟 מקומות פופולריים",
        'about': "ℹ️ אודות",
        'choose_area': "📍 בחר אזור בתל אביב לחיפוש הפי אוור:",
        'share_location': "📍 שתף את המיקום שלך למציאת מקומות קרובים",
        'no_current_hours': "😔 אין הפי אוור פעיל כרגע!\n\nהאם תרצה לראות את כל ההפי אוורס הזמינים?",
        'current_hours_header': "🎉 הפי אוור פעיל כרגע ({})",
        'popular_header': "🌟 ההפי אוורס הפופולריים בתל אביב:",
        'area_header': "🎉 הפי אוור ב{}:",
        'nearby_header': "📍 מקומות קרובים אליך:",
        'more_options': "\nרוצה לראות עוד אפשרויות? השתמש בכפתורים למטה!",
        'refresh': "🔄 רענן",
        'new_search': "🔍 חיפוש חדש",
        'main_menu': "🏠 תפריט ראשי",
        'about_text': (
            "🍻 *Happy Hour TLV Bot*\n\n"
            "המדריך האולטימטיבי למבצעי שתייה בתל אביב!\n\n"
            "תכונות:\n"
            "• עדכוני הפי אוור בזמן אמת\n"
            "• חיפוש לפי מיקום\n"
            "• מציאת מקומות קרובים\n"
            "• מידע מפורט על המקומות\n"
            "• אינדיקציית טווח מחירים\n"
            "• תיאור האווירה והמקום\n\n"
            "השתמש ב /start בכל עת כדי להתחיל מחדש!\n\n"
            "לחיים! 🥂"
        ),
        'welcome_back': "ברוך שובך! מה תרצה לעשות?",
        'change_language': "🌐 שנה שפה",
        'locations': {
            "Dizengoff": "דיזנגוף",
            "Florentin": "פלורנטין",
            "Rothschild": "רוטשילד",
            "Carmel Market": "שוק הכרמל"
        },
        'error_loading_venues': "❌ מצטער, לא יכולתי לטעון את המקומות כרגע. אנא נסה שוב מאוחר יותר.",
        'error_processing_location': "❌ מצטער, הייתה בעיה בעיבוד המיקום שלך. אנא נסה שוב.",
        'no_nearby_venues': "😔 לא נמצאו מקומות בקרבת מקום. נסה להגדיל את רדיוס החיפוש או לבדוק אזור אחר.",
        'current_happy_hour': "🔥 כרגע בהפי אוור!",
        'distance_away': "📍 {} ק\"מ מכאן",
        'choose_radius': "📍 בחר רדיוס חיפוש:",
        'choose_vibe': "🌟 בחר אווירה לחיפוש מקומות:",
        'no_vibe_venues': "😔 לא נמצאו מקומות עם אווירה זו. נסה אחרת!",
        'vibe_header': "🌟 מקומות עם אווירת {}:",
        'vibes': {
            "Chill": "רגוע",
            "Trendy": "טרנדי",
            "Upscale": "יוקרתי",
            "Casual": "יומיומי"
        },
    }
}

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points in kilometers"""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def get_google_maps_link(coords):
    """Generate Google Maps link for navigation"""
    return f"https://www.google.com/maps/dir/?api=1&destination={coords}"

def get_text(key, lang, *args):
    """Get translated text"""
    return TRANSLATIONS[lang][key].format(*args) if args else TRANSLATIONS[lang][key]

def create_location_keyboard(lang):
    """Create keyboard with location sharing button and options"""
    keyboard = [
        [KeyboardButton(get_text('share_location', lang), request_location=True)],
        [
            InlineKeyboardButton("📍 1km", callback_data="radius_1"),
            InlineKeyboardButton("📍 2km", callback_data="radius_2"),
            InlineKeyboardButton("📍 5km", callback_data="radius_5")
        ],
        [InlineKeyboardButton(get_text('main_menu', lang), callback_data='main_menu')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def format_place_details(place, area, lang):
    """Format place details with navigation link"""
    name = place.get('name', '')
    address = place.get('address', '')
    latitude = place.get('latitude', '')
    longitude = place.get('longitude', '')
    deal = place.get('deal', '')
    hours = place.get('hours', '')
    phone = place.get('phone', '')
    website = place.get('website', '')
    
    coords = f"{latitude},{longitude}" if latitude and longitude else ''
    maps_link = get_google_maps_link(coords) if coords else None
    
    details = f"*{name}*\n"
    details += f"📍 {address}\n"
    if hours:
        details += f"⏰ Hours: {hours}\n"
    if deal:
        details += f"🎉 Deal: {deal}\n"
    if phone:
        details += f"📞 Phone: {phone}\n"
    if website:
        details += f"🌐 Website: {website}\n"
    if maps_link:
        details += f"\n🗺 [Open in Maps]({maps_link})"
    
    return details

async def load_venues():
    """Load venues from JSON file with error handling"""
    try:
        logger.info(f"Attempting to load venues from: {VENUES_FILE}")
        with open(VENUES_FILE, 'r', encoding='utf-8') as f:
            venues = json.load(f)
            logger.info(f"Successfully loaded {len(venues)} venues")
            return venues
    except FileNotFoundError:
        logger.error(f"Venues file not found at: {VENUES_FILE}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading venues: {str(e)}")
        return None

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle received location and find nearby venues"""
    try:
        user_location = update.message.location
        lang = context.user_data.get('lang', 'en')
        radius = context.user_data.get('search_radius', 2)  # Default 2km radius
        
        venues = await load_venues()
        if not venues:
            await update.message.reply_text(get_text('error_loading_venues', lang))
            return CHOOSING_ACTION
        
        # Calculate distances and sort venues
        nearby_venues = []
        for venue in venues:
            if venue.get('latitude') and venue.get('longitude'):
                distance = calculate_distance(
                    user_location.latitude,
                    user_location.longitude,
                    venue['latitude'],
                    venue['longitude']
                )
                if distance <= radius:  # Within specified radius
                    venue['distance'] = distance
                    nearby_venues.append(venue)
        
        # Sort by distance
        nearby_venues.sort(key=lambda x: x['distance'])
        
        if not nearby_venues:
            await update.message.reply_text(get_text('no_nearby_venues', lang))
            return CHOOSING_ACTION
        
        # Format and send nearby venues
        message = get_text('nearby_header', lang) + "\n\n"
        for venue in nearby_venues[:5]:  # Show top 5 closest venues
            message += format_place_details(venue, None, lang)
            message += f"\n📍 {venue['distance']:.1f}km away\n\n"
        
        keyboard = create_refresh_keyboard(lang)
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        return CHOOSING_ACTION
        
    except Exception as e:
        logger.error(f"Error handling location: {str(e)}")
        await update.message.reply_text(get_text('error_processing_location', lang))
        return CHOOSING_ACTION

def create_location_keyboard(lang):
    """Create keyboard with all locations in the selected language."""
    keyboard = []
    row = []
    for idx, location in enumerate(SAMPLE_HAPPY_HOURS.keys()):
        translated_location = TRANSLATIONS[lang]['locations'][location]
        row.append(InlineKeyboardButton(translated_location, callback_data=f"loc_{location.lower()}"))
        if (idx + 1) % 2 == 0 or idx == len(SAMPLE_HAPPY_HOURS.keys()) - 1:
            keyboard.append(row)
            row = []
    keyboard.append([InlineKeyboardButton(get_text('main_menu', lang), callback_data="start")])
    return keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the conversation and ask user to choose a language."""
    keyboard = [
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
            InlineKeyboardButton("עברית 🇮🇱", callback_data="lang_he"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose your language / בחר את השפה שלך", reply_markup=reply_markup)
    return CHOOSING_LANGUAGE

def create_main_menu_keyboard(lang):
    """Create the main menu keyboard with translated buttons."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_text('find_happy_hour', lang), callback_data="find_happy_hour"),
            InlineKeyboardButton(get_text('find_nearby', lang), callback_data="find_nearby"),
        ],
        [
            InlineKeyboardButton(get_text('current_happy_hours', lang), callback_data="current_happy_hours"),
            InlineKeyboardButton(get_text('popular_places', lang), callback_data="popular_places"),
        ],
        [
            InlineKeyboardButton("🌟 Find by Vibe", callback_data="find_by_vibe"),
            InlineKeyboardButton(get_text('about', lang), callback_data="about"),
        ],
        [InlineKeyboardButton(get_text('change_language', lang), callback_data="change_lang")]
    ])

def create_refresh_keyboard(lang):
    """Create keyboard with refresh and new search options."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_text('refresh', lang), callback_data="refresh"),
            InlineKeyboardButton(get_text('find_happy_hour', lang), callback_data="find_happy_hour"),
        ],
        [InlineKeyboardButton(get_text('main_menu', lang), callback_data="main_menu")]
    ])

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection and show main menu."""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang
    
    keyboard = create_main_menu_keyboard(lang)
    await query.edit_message_text(text=get_text("welcome", lang), reply_markup=keyboard)
    return CHOOSING_ACTION

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu actions."""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get("lang", "en")
    
    if query.data == "find_happy_hour":
        keyboard = create_area_keyboard(lang)
        await query.edit_message_text(
            text=get_text("choose_area", lang),
            reply_markup=keyboard
        )
        return CHOOSING_LOCATION
    elif query.data == "find_nearby":
        keyboard = create_location_keyboard(lang)
        await query.edit_message_text(
            text=get_text("share_location", lang),
            reply_markup=keyboard
        )
        return WAITING_FOR_LOCATION
    elif query.data == "find_by_vibe":
        keyboard = create_vibe_keyboard(lang)
        await query.edit_message_text(
            text=get_text("choose_vibe", lang),
            reply_markup=keyboard
        )
        return CHOOSING_VIBE
    elif query.data.startswith("radius_"):
        radius = int(query.data.split("_")[1])
        context.user_data["search_radius"] = radius
        keyboard = create_location_keyboard(lang)
        await query.edit_message_text(
            text=get_text("share_location", lang),
            reply_markup=keyboard
        )
        return WAITING_FOR_LOCATION
    elif query.data == "refresh":
        # Re-run the last action based on the current state
        state = context.user_data.get("last_state")
        if state == "area":
            area = context.user_data.get("last_area")
            if area:
                query.data = f"area_{area.lower()}"
                return await show_area_venues(update, context)
        return await handle_action(update, context)
    elif query.data == "current_happy_hours":
        return await show_current_happy_hours(update, context)
    elif query.data == "popular_places":
        return await show_popular_places(update, context)
    elif query.data == "about":
        keyboard = create_main_menu_keyboard(lang)
        await query.edit_message_text(
            text=get_text("about_text", lang),
            reply_markup=keyboard
        )
        return CHOOSING_ACTION
    elif query.data == "main_menu":
        keyboard = create_main_menu_keyboard(lang)
        await query.edit_message_text(
            text=get_text("welcome_back", lang),
            reply_markup=keyboard
        )
        return CHOOSING_ACTION

async def show_area_venues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show venues in the selected area."""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    area = query.data.replace('area_', '').replace('_', ' ').title()
    
    # Store the last state and area for refresh functionality
    context.user_data["last_state"] = "area"
    context.user_data["last_area"] = area
    
    venues = await load_venues()
    if not venues:
        await query.edit_message_text(
            text=get_text('error_loading_venues', lang),
            reply_markup=create_main_menu_keyboard(lang)
        )
        return CHOOSING_ACTION
    
    # Filter venues by area (more flexible matching)
    area_venues = [
        venue for venue in venues 
        if area.lower() in venue.get('address', '').lower() or 
           area.lower() in venue.get('name', '').lower()
    ]
    
    if not area_venues:
        await query.edit_message_text(
            text=f"No venues found in {area}",
            reply_markup=create_refresh_keyboard(lang)
        )
        return CHOOSING_ACTION
    
    # Format message with venues
    message = get_text('area_header', lang, area) + "\n\n"
    for venue in area_venues[:5]:  # Show top 5 venues
        message += format_place_details(venue, area, lang)
        message += "\n\n"
    
    keyboard = create_refresh_keyboard(lang)
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    return CHOOSING_ACTION

def create_area_keyboard(lang):
    """Create keyboard with area selection buttons."""
    areas = ["Dizengoff", "Florentin", "Rothschild", "Carmel_Market"]
    keyboard = []
    row = []
    
    for idx, area in enumerate(areas):
        translated_area = TRANSLATIONS[lang]['locations'][area.replace('_', ' ')]
        row.append(InlineKeyboardButton(
            translated_area,
            callback_data=f"area_{area.lower()}"
        ))
        if (idx + 1) % 2 == 0 or idx == len(areas) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton(get_text('main_menu', lang), callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

async def show_vibe_venues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show venues with the selected vibe."""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    vibe = query.data.replace('vibe_', '').replace('_', ' ').title()
    
    try:
        # Load venues from JSON file
        with open('data/happyhourstlv_enriched.json', 'r', encoding='utf-8') as f:
            venues = json.load(f)
        
        # Filter venues by vibe
        vibe_venues = [venue for venue in venues if vibe.lower() in venue.get('vibe', {}).get(lang, '').lower()]
        
        if not vibe_venues:
            await query.edit_message_text(
                text=f"No venues found with {vibe} vibe",
                reply_markup=create_refresh_keyboard(lang)
            )
            return CHOOSING_ACTION
        
        # Check current time for happy hour status
        current_time = datetime.now().strftime("%H:%M")
        
        # Format message with venues
        message = f"🌟 Venues with {vibe} vibe:\n\n"
        for venue in vibe_venues[:5]:  # Show top 5 venues
            message += format_place_details(venue, None, lang)
            if venue.get('happy_hour'):
                start_time, end_time = venue['happy_hour'].split("-")
                if start_time <= current_time <= end_time:
                    message += f"\n🔥 {get_text('current_happy_hour', lang)}"
            message += "\n\n"
        
        keyboard = create_refresh_keyboard(lang)
        await query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing vibe venues: {str(e)}")
        await query.edit_message_text(
            text=get_text('error_loading_venues', lang),
            reply_markup=create_main_menu_keyboard(lang)
        )
    
    return CHOOSING_ACTION

def create_vibe_keyboard(lang):
    """Create keyboard with vibe selection buttons."""
    vibes = ["Chill", "Trendy", "Upscale", "Casual"]
    keyboard = []
    row = []
    
    for idx, vibe in enumerate(vibes):
        row.append(InlineKeyboardButton(
            f"🌟 {vibe}",
            callback_data=f"vibe_{vibe.lower()}"
        ))
        if (idx + 1) % 2 == 0 or idx == len(vibes) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton(get_text('main_menu', lang), callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANGUAGE: [
                CallbackQueryHandler(choose_language, pattern="^lang_")
            ],
            CHOOSING_ACTION: [
                CallbackQueryHandler(handle_action),
                MessageHandler(filters.LOCATION, handle_location)
            ],
            CHOOSING_LOCATION: [
                CallbackQueryHandler(show_area_venues, pattern="^area_")
            ],
            CHOOSING_VIBE: [
                CallbackQueryHandler(show_vibe_venues, pattern="^vibe_")
            ],
            WAITING_FOR_LOCATION: [
                MessageHandler(filters.LOCATION, handle_location),
                CallbackQueryHandler(handle_action, pattern="^radius_")
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main() 
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)
import urllib.parse

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
CHOOSING_LANGUAGE, CHOOSING_ACTION, CHOOSING_LOCATION, CHOOSING_VIBE = range(4)

# Translations dictionary
TRANSLATIONS = {
    'en': {
        'welcome': (
            "Welcome to Happy Hour TLV Bot! 🍻\n\n"
            "I'm your personal guide to the best drink deals in Tel Aviv!\n\n"
            "Here's what I can help you with:\n"
            "🔍 Find happy hours by location\n"
            "⏰ See what's happening right now\n"
            "🌟 Check out popular spots\n"
            "ℹ️ Learn more about the bot\n\n"
            "What would you like to do?"
        ),
        'find_happy_hour': "🔍 Find Happy Hour",
        'current_happy_hours': "⏰ Current Happy Hours",
        'popular_places': "🌟 Popular Places",
        'about': "ℹ️ About",
        'choose_area': "📍 Choose an area in Tel Aviv to explore happy hours:",
        'no_current_hours': "😔 No happy hours currently running!\n\nWould you like to see all available happy hours instead?",
        'current_hours_header': "🎉 Current happy hours (at {})",
        'popular_header': "🌟 Most Popular Happy Hours in Tel Aviv:",
        'area_header': "🎉 Happy Hours in {}:",
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
    },
    'he': {
        'welcome': (
            "ברוכים הבאים לבוט Happy Hour TLV! 🍻\n\n"
            "אני המדריך האישי שלך למבצעי השתייה הטובים ביותר בתל אביב!\n\n"
            "הנה במה אני יכול לעזור:\n"
            "🔍 חיפוש הפי אוור לפי מיקום\n"
            "⏰ ראה מה קורה עכשיו\n"
            "🌟 בדוק מקומות פופולריים\n"
            "ℹ️ מידע נוסף על הבוט\n\n"
            "מה תרצה לעשות?"
        ),
        'find_happy_hour': "🔍 חפש הפי אוור",
        'current_happy_hours': "⏰ הפי אוור עכשיו",
        'popular_places': "🌟 מקומות פופולריים",
        'about': "ℹ️ אודות",
        'choose_area': "📍 בחר אזור בתל אביב לחיפוש הפי אוור:",
        'no_current_hours': "😔 אין הפי אוור פעיל כרגע!\n\nהאם תרצה לראות את כל ההפי אוורס הזמינים?",
        'current_hours_header': "🎉 הפי אוור פעיל כרגע ({})",
        'popular_header': "🌟 ההפי אוורס הפופולריים בתל אביב:",
        'area_header': "🎉 הפי אוור ב{}:",
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
    }
}

# Sample happy hour data with more locations and details
SAMPLE_HAPPY_HOURS = {
    "Dizengoff": [
        {
            "name": {"en": "Beer Garden", "he": "ביר גארדן"},
            "address": "Dizengoff 100",
            "coords": "32.0778,34.7732",
            "happy_hour": "17:00-19:00",
            "deals": {
                "en": "50% off all beers, 1+1 on cocktails",
                "he": "50% הנחה על כל הבירות, 1+1 על קוקטיילים"
            },
            "vibe": {"en": "Casual", "he": "לא פורמלי"},
            "price_range": "$$",
            "description": {
                "en": "Relaxed garden atmosphere with a great selection of craft beers",
                "he": "אווירת גן רגועה עם מבחר בירות מעולה"
            }
        },
        {
            "name": {"en": "Wine Bar", "he": "בר יין"},
            "address": "Dizengoff 150",
            "coords": "32.0785,34.7735",
            "happy_hour": "18:00-20:00",
            "deals": {
                "en": "30% off wine bottles, free tapas",
                "he": "30% הנחה על בקבוקי יין, טאפס חינם"
            },
            "vibe": {"en": "Upscale", "he": "יוקרתי"},
            "price_range": "$$$",
            "description": {
                "en": "Elegant wine bar with an extensive selection of international wines",
                "he": "בר יין אלגנטי עם מבחר יינות בינלאומי"
            }
        },
        {
            "name": {"en": "Sunset Lounge", "he": "סאנסט לאונג'"},
            "address": "Dizengoff 220",
            "coords": "32.0795,34.7738",
            "happy_hour": "16:00-19:00",
            "deals": {
                "en": "40% off cocktails, half-price appetizers",
                "he": "40% הנחה על קוקטיילים, מנות ראשונות בחצי מחיר"
            },
            "vibe": {"en": "Trendy", "he": "טרנדי"},
            "price_range": "$$$",
            "description": {
                "en": "Rooftop bar with stunning sunset views and creative cocktails",
                "he": "בר גג עם נוף שקיעה מדהים וקוקטיילים יצירתיים"
            }
        }
    ],
    "Florentin": [
        {
            "name": {"en": "Hipster Hub", "he": "היפסטר האב"},
            "address": "Florentin 20",
            "coords": "32.0565,34.7682",
            "happy_hour": "16:00-19:00",
            "deals": {
                "en": "1+1 on draft beers, discounted snacks",
                "he": "1+1 על בירות מהחבית, חטיפים מוזלים"
            },
            "vibe": {"en": "Alternative", "he": "אלטרנטיבי"},
            "price_range": "$",
            "description": {
                "en": "Artistic venue with local craft beers and indie music",
                "he": "מקום אומנותי עם בירות קראפט מקומיות ומוזיקת אינדי"
            }
        },
        {
            "name": {"en": "The Local", "he": "הלוקאל"},
            "address": "Florentin 55",
            "coords": "32.0571,34.7685",
            "happy_hour": "17:00-20:00",
            "deals": {
                "en": "25% off all drinks, special happy hour menu",
                "he": "25% הנחה על כל המשקאות, תפריט הפי אוור מיוחד"
            },
            "vibe": {"en": "Casual", "he": "לא פורמלי"},
            "price_range": "$",
            "description": {
                "en": "Neighborhood favorite with great food and friendly atmosphere",
                "he": "מקום שכונתי אהוב עם אוכל טוב ואווירה חברותית"
            }
        }
    ],
    "Rothschild": [
        {
            "name": {"en": "Cocktail Embassy", "he": "קוקטייל אמבסי"},
            "address": "Rothschild 45",
            "coords": "32.0632,34.7721",
            "happy_hour": "18:00-21:00",
            "deals": {
                "en": "1+1 on signature cocktails, 30% off wine",
                "he": "1+1 על קוקטיילים מיוחדים, 30% הנחה על יין"
            },
            "vibe": {"en": "Upscale", "he": "יוקרתי"},
            "price_range": "$$$",
            "description": {
                "en": "Sophisticated cocktail bar with expert mixologists",
                "he": "בר קוקטיילים מתוחכם עם ברמנים מומחים"
            }
        },
        {
            "name": {"en": "Boulevard Social", "he": "בולווארד סושיאל"},
            "address": "Rothschild 90",
            "coords": "32.0645,34.7728",
            "happy_hour": "17:00-19:30",
            "deals": {
                "en": "40% off all drinks, complimentary bar snacks",
                "he": "40% הנחה על כל המשקאות, חטיפי בר חינם"
            },
            "vibe": {"en": "Trendy", "he": "טרנדי"},
            "price_range": "$$",
            "description": {
                "en": "Popular spot with boulevard views and great atmosphere",
                "he": "מקום פופולרי עם נוף לשדרה ואווירה מעולה"
            }
        }
    ],
    "Carmel Market": [
        {
            "name": {"en": "Market Bar", "he": "בר השוק"},
            "address": "HaCarmel 40",
            "coords": "32.0685,34.7685",
            "happy_hour": "15:00-18:00",
            "deals": {
                "en": "Local beer specials, 1+1 on house wine",
                "he": "מבצעים על בירה מקומית, 1+1 על יין הבית"
            },
            "vibe": {"en": "Casual", "he": "לא פורמלי"},
            "price_range": "$",
            "description": {
                "en": "Authentic market vibes with local flavors",
                "he": "אווירת שוק אותנטית עם טעמים מקומיים"
            }
        },
        {
            "name": {"en": "Shuk Social", "he": "שוק סושיאל"},
            "address": "HaCarmel 11",
            "coords": "32.0681,34.7682",
            "happy_hour": "16:00-19:00",
            "deals": {
                "en": "Beer buckets, half-price mezze platters",
                "he": "דליי בירה, מארזי מזה בחצי מחיר"
            },
            "vibe": {"en": "Alternative", "he": "אלטרנטיבי"},
            "price_range": "$",
            "description": {
                "en": "Hidden gem with great food and drink combinations",
                "he": "פנינה נסתרת עם שילובי אוכל ושתייה מעולים"
            }
        }
    ]
}

def get_google_maps_link(coords):
    """Generate Google Maps link from coordinates."""
    return f"https://www.google.com/maps?q={coords}"

def get_text(key, lang, *args):
    """Get translated text with optional formatting."""
    text = TRANSLATIONS[lang][key]
    if args:
        return text.format(*args)
    return text

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

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection buttons."""
    keyboard = [
        [
            InlineKeyboardButton("English 🇺🇸", callback_data="lang_en"),
            InlineKeyboardButton("עברית 🇮🇱", callback_data="lang_he"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Please choose your language:\nאנא בחר את השפה שלך:",
        reply_markup=reply_markup
    )
    return CHOOSING_LANGUAGE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the bot and show language selection."""
    return await choose_language(update, context)

def format_place_details(place, area, lang):
    """Format place details with emojis and styling."""
    maps_link = get_google_maps_link(place['coords'])
    return (
        f"🏢 *{place['name'][lang]}* ({area})\n"
        f"📍 [{place['address']}]({maps_link})\n"
        f"⏰ {place['happy_hour']}\n"
        f"💰 {place['deals'][lang]}\n"
        f"🎯 {place['vibe'][lang]}\n"
        f"💳 {place['price_range']}\n"
        f"📝 {place['description'][lang]}\n"
    )

def create_main_menu_keyboard(lang):
    """Create the main menu keyboard with translated buttons."""
    return [
        [
            InlineKeyboardButton(get_text('find_happy_hour', lang), callback_data="find"),
            InlineKeyboardButton(get_text('current_happy_hours', lang), callback_data="current"),
        ],
        [
            InlineKeyboardButton(get_text('popular_places', lang), callback_data="popular"),
            InlineKeyboardButton(get_text('about', lang), callback_data="about"),
        ],
        [InlineKeyboardButton(get_text('change_language', lang), callback_data="change_lang")]
    ]

def create_refresh_keyboard(lang):
    """Create keyboard with refresh and new search options."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_text('refresh', lang), callback_data="refresh"),
            InlineKeyboardButton(get_text('new_search', lang), callback_data="find"),
        ],
        [InlineKeyboardButton(get_text('main_menu', lang), callback_data="start")]
    ])

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    # Handle language selection
    if query.data.startswith("lang_"):
        lang = query.data.replace("lang_", "")
        context.user_data['language'] = lang
        keyboard = create_main_menu_keyboard(lang)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=get_text('welcome', lang),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return CHOOSING_ACTION

    # Get user's language preference
    lang = context.user_data.get('language', 'en')

    if query.data == "change_lang":
        keyboard = [
            [
                InlineKeyboardButton("English 🇺🇸", callback_data="lang_en"),
                InlineKeyboardButton("עברית 🇮🇱", callback_data="lang_he"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Please choose your language:\nאנא בחר את השפה שלך:",
            reply_markup=reply_markup
        )
        return CHOOSING_LANGUAGE

    if query.data == "start":
        keyboard = create_main_menu_keyboard(lang)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=get_text('welcome', lang),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return CHOOSING_ACTION

    elif query.data == "find":
        keyboard = create_location_keyboard(lang)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=get_text('choose_area', lang),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return CHOOSING_LOCATION
    
    elif query.data == "current":
        current_time = datetime.now().strftime("%H:%M")
        message = get_text('current_hours_header', lang, current_time) + "\n\n"
        found = False
        
        for area, places in SAMPLE_HAPPY_HOURS.items():
            for place in places:
                start_time, end_time = place["happy_hour"].split("-")
                if start_time <= current_time <= end_time:
                    message += format_place_details(place, area, lang) + "\n"
                    found = True
        
        if not found:
            message = get_text('no_current_hours', lang)
        
        await query.edit_message_text(
            text=message,
            reply_markup=create_refresh_keyboard(lang),
            parse_mode='Markdown'
        )
        return CHOOSING_ACTION

    elif query.data == "popular":
        message = get_text('popular_header', lang) + "\n\n"
        # Showing 3 curated options with different vibes
        popular_places = [
            ("Cocktail Embassy", "Rothschild"),
            ("Beer Garden", "Dizengoff"),
            ("Market Bar", "Carmel Market")
        ]
        
        for place_name, area in popular_places:
            for place in SAMPLE_HAPPY_HOURS[area]:
                if place["name"] == place_name:
                    message += format_place_details(place, area, lang) + "\n"
        
        await query.edit_message_text(
            text=message,
            reply_markup=create_refresh_keyboard(lang),
            parse_mode='Markdown'
        )
        return CHOOSING_ACTION
    
    elif query.data.startswith("loc_"):
        location = query.data.replace("loc_", "").capitalize()
        if location.lower() == "carmel market":
            location = "Carmel Market"
            
        if location in SAMPLE_HAPPY_HOURS:
            message = get_text('area_header', lang, location) + "\n\n"
            places = SAMPLE_HAPPY_HOURS[location]
            
            # Show 3 random places if more than 3 exist
            if len(places) > 3:
                import random
                places = random.sample(places, 3)
            
            for place in places:
                message += format_place_details(place, location, lang) + "\n"
                
            message += get_text('more_options', lang)
            
            await query.edit_message_text(
                text=message,
                reply_markup=create_refresh_keyboard(lang),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                text="Sorry, no happy hours found in this area.",
                reply_markup=create_refresh_keyboard(lang)
            )
        return CHOOSING_ACTION

    elif query.data == "refresh":
        # Simulate refreshing by showing different options if available
        return await button_callback(update, context)  # Re-run the last command
    
    elif query.data == "about":
        await query.edit_message_text(
            text=get_text('about_text', lang),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="start")]]),
            parse_mode='Markdown'
        )
        return CHOOSING_ACTION

async def delete_webhook_and_start(application: Application):
    """Delete webhook and start polling."""
    try:
        # Initialize the application first
        await application.initialize()
        # Then delete webhook and start polling
        await application.bot.delete_webhook(drop_pending_updates=True)
        await application.start()
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

async def main():
    """Start the bot."""
    # Load token from environment variable
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError("No TELEGRAM_TOKEN found in environment variables")

    # Create application
    application = Application.builder().token(token).build()

    # Add handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANGUAGE: [CallbackQueryHandler(button_callback)],
            CHOOSING_ACTION: [CallbackQueryHandler(button_callback)],
            CHOOSING_LOCATION: [CallbackQueryHandler(button_callback)],
            CHOOSING_VIBE: [CallbackQueryHandler(button_callback)],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)

    # Run the bot
    await delete_webhook_and_start(application)

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 
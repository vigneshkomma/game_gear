# Gaming Marketplace

A Django-based online marketplace for buying and selling gaming-related gear — discs, graphics cards, monitors, keyboards, and similar items. Currently scoped for **India only**.

## Features

- User accounts for buyers and sellers
- Listings for gaming gear (discs, GPUs, monitors, keyboards, etc.)
- Listing status tracking (available / purchased)
- Browse and search marketplace listings
- India-only shipping/location scope for v1

## Tech Stack

- **Backend:** Django (Python)
- **Database:** SQLite3





## Getting Started

```bash
# Clone the repository
git clone <repo-url>
cd gaming-marketplace

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run the development server
python manage.py runserver
```

## Scope

This project targets the **Indian market only** for its initial release. Expansion to other regions is not currently planned for v1.

## License

TBD
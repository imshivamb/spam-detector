import os
import random
import django
import sys
import time
from pathlib import Path
from datetime import timedelta

# Add the project root directory to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
django.setup()

# Import models after Django setup
from django.utils import timezone
from django.db import transaction
from apps.users.models import User
from apps.contacts.models import Contact
from apps.spam.models import SpamReport

# Sample data
NAMES = [
    "John Smith", "Emma Wilson", "Michael Brown", "Sarah Davis", "James Johnson",
    "Lisa Anderson", "David Miller", "Jennifer Taylor", "Robert Jones", "Maria Garcia",
    "William Martinez", "Elizabeth Thomas", "Richard White", "Susan Moore", "Joseph Lee",
    "Margaret Wilson", "Charles Davis", "Patricia Brown", "Thomas Anderson", "Linda Martin"
]

# Phone number prefixes for different regions
PHONE_PREFIXES = ['+1', '+44', '+91', '+61', '+86']

def generate_phone_number(prefix):
    """Generate a random phone number with given prefix"""
    number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    return f"{prefix}{number}"

def create_users(num_users=20):
    """Create sample users"""
    print("Creating users...")
    users = []
    used_phones = set()
    used_emails = set()
    
    for i in range(num_users):
        # Generate unique phone number
        while True:
            prefix = random.choice(PHONE_PREFIXES)
            phone = generate_phone_number(prefix)
            if phone not in used_phones:
                used_phones.add(phone)
                break
        
        name = random.choice(NAMES)
        
        # Generate unique email with timestamp and random number
        if random.random() > 0.3:  # 70% chance of having email
            timestamp = int(time.time())
            random_num = random.randint(1000, 9999)
            email = f"{name.lower().replace(' ', '.')}.{timestamp}.{random_num}@example.com"
            used_emails.add(email)
        else:
            email = None
        
        try:
            user = User.objects.create_user(
                name=name,
                phone_number=phone,
                email=email,
                password="testpass123"  # Simple password for testing
            )
            users.append(user)
            print(f"Created user: {user.name} ({user.phone_number}){' with email: ' + email if email else ''}")
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            continue
    
    return users

def create_contacts(users, avg_contacts_per_user=10):
    """Create sample contacts for users"""
    print("\nCreating contacts...")
    created_contacts = []
    
    for user in users:
        num_contacts = random.randint(avg_contacts_per_user - 5, avg_contacts_per_user + 5)
        
        for _ in range(num_contacts):
            try:
                name = random.choice(NAMES)
                prefix = random.choice(PHONE_PREFIXES)
                phone = generate_phone_number(prefix)
                
                # Check if this user already has this phone number as a contact
                if not Contact.objects.filter(user=user, phone_number=phone).exists():
                    contact = Contact.objects.create(
                        user=user,
                        name=name,
                        phone_number=phone
                    )
                    created_contacts.append(contact)
                    print(f"Created contact: {contact.name} ({contact.phone_number}) for user {user.name}")
            except Exception as e:
                print(f"Error creating contact: {str(e)}")
                continue
    
    return created_contacts

def create_spam_reports(users, spam_probability=0.2):
    """Create sample spam reports"""
    print("\nCreating spam reports...")
    reports = []
    all_contacts = Contact.objects.all()
    
    if not all_contacts:
        print("No contacts available for spam reports")
        return reports

    for user in users:
        try:
            # Get random contacts to mark as spam
            num_contacts_to_spam = random.randint(1, min(5, all_contacts.count()))
            contacts_to_spam = random.sample(list(all_contacts), k=num_contacts_to_spam)
            
            for contact in contacts_to_spam:
                if random.random() < spam_probability:
                    # Check if user hasn't already reported this number
                    if not SpamReport.objects.filter(
                        reporter=user, 
                        phone_number=contact.phone_number,
                        is_active=True
                    ).exists():
                        report = SpamReport.objects.create(
                            reporter=user,
                            phone_number=contact.phone_number,
                            is_active=True
                        )
                        reports.append(report)
                        print(f"Created spam report by {user.name} for number {contact.phone_number}")
        except Exception as e:
            print(f"Error creating spam report: {str(e)}")
            continue
    
    return reports

@transaction.atomic
def run():
    """Main function to populate the database"""
    try:
        # Clean existing data (except superuser)
        print("Cleaning existing data...")
        SpamReport.objects.all().delete()
        Contact.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        # Create new data
        users = create_users(20)  # Create 20 users
        if users:
            contacts = create_contacts(users, 10)  # Average 10 contacts per user
            if contacts:
                reports = create_spam_reports(users, 0.2)  # 20% chance of spam report
            
            # Print summary
            print("\nDatabase populated successfully!")
            print(f"Created:")
            print(f"- {len(users)} users")
            print(f"- {Contact.objects.count()} contacts")
            print(f"- {SpamReport.objects.count()} spam reports")
        else:
            print("Failed to create users. Database population aborted.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    print("Starting database population...")
    run()
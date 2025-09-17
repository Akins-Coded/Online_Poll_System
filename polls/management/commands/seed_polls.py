from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from polls.models import Poll, Option, Vote
from faker import Faker
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with fake polls, options, and votes."

    def add_arguments(self, parser):
        parser.add_argument('--polls', type=int, default=5, help="Number of polls to create")
        parser.add_argument('--users', type=int, default=10, help="Number of users to create")
        parser.add_argument('--votes', type=int, default=50, help="Number of votes to create")

    def handle(self, *args, **options):
        fake = Faker()

        num_polls = options['polls']
        num_users = options['users']
        num_votes = options['votes']

        # Create Users
        users = []
        for _ in range(num_users):
            user = User.objects.create_user(
                email=fake.email(),
                password="password123",
                first_name=fake.first_name(),
                surname=fake.last_name()
            )
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(users)} users."))

        # Create Polls & Options
        polls = []
        for _ in range(num_polls):
            poll = Poll.objects.create(
                title=fake.sentence(nb_words=6),
                description=fake.text(max_nb_chars=200),
                created_by=random.choice(users)
            )
            # Ensure at least 2 options, sometimes more (2–6)
            num_options = random.randint(2, 6)
            for _ in range(num_options):
                Option.objects.create(
                    poll=poll,
                    text=fake.word().capitalize()
                )
            polls.append(poll)
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(polls)} polls with varied options."))

        # Create Votes
        all_options = list(Option.objects.all())
        votes = []
        for _ in range(num_votes):
            option = random.choice(all_options)
            user = random.choice(users)
            # Prevent duplicate votes on the same poll
            if not Vote.objects.filter(poll=option.poll, user=user).exists():
                vote = Vote.objects.create(
                    poll=option.poll,
                    option=option,
                    user=user
                )
                votes.append(vote)
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(votes)} votes."))

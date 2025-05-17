"""
Habit Tracker Application

This module implements a habit tracking application with features to:
- Create and manage habits with different periodicities
- Complete habit tasks
- Track habit streaks
- Analyze habits using functional programming

Author: Jeanni Labuschagne
Date: May 17, 2025
"""

import os
import sqlite3
import uuid
from datetime import datetime, timedelta
import click
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
from functools import reduce, partial
import itertools

# ========== Database Setup ==========

def get_db_path() -> str:
    """Get the path to the SQLite database file."""
    # Store database in user's home directory
    db_dir = os.path.join(os.path.expanduser("~"), ".habit_tracker")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "habits.db")

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Create habits table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS habits (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        periodicity TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Create completions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS completions (
        id TEXT PRIMARY KEY,
        habit_id TEXT NOT NULL,
        completed_at TEXT NOT NULL,
        FOREIGN KEY (habit_id) REFERENCES habits(id)
    )
    ''')
    
    conn.commit()
    conn.close()

# ========== Classes ==========

class Habit:
    """
    Class representing a habit to be tracked.
    
    Attributes:
        id (str): Unique identifier for the habit
        name (str): Name of the habit
        description (str): Detailed description of the habit
        periodicity (str): Frequency of the habit ('daily' or 'weekly')
        created_at (datetime): When the habit was created
        completions (list): List of completion timestamps
    """
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        periodicity: str,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        completions: Optional[List[datetime]] = None
    ):
        """
        Initialize a new Habit instance.
        
        Args:
            name: Name of the habit
            description: Detailed description of the habit
            periodicity: Frequency ('daily' or 'weekly')
            id: Unique identifier (auto-generated if None)
            created_at: Creation timestamp (current time if None)
            completions: List of completion timestamps (empty list if None)
        """
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.description = description
        
        if periodicity not in ['daily', 'weekly']:
            raise ValueError("Periodicity must be 'daily' or 'weekly'")
        self.periodicity = periodicity
        
        self.created_at = created_at if created_at else datetime.now()
        self.completions = completions if completions else []
    
    def complete_task(self) -> None:
        """Mark the habit as completed for the current time."""
        self.completions.append(datetime.now())
    
    def is_task_completed_for_period(self, target_date: datetime) -> bool:
        """
        Check if the habit was completed during a specific period.
        
        Args:
            target_date: The date to check completion for
            
        Returns:
            bool: True if completed during the period, False otherwise
        """
        if self.periodicity == 'daily':
            # Check if completed on this specific day
            return any(
                c.date() == target_date.date()
                for c in self.completions
            )
        else:  # weekly
            # Find the start of the week (Monday)
            start_of_week = target_date.date() - timedelta(days=target_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            return any(
                start_of_week <= c.date() <= end_of_week
                for c in self.completions
            )
    
    def get_current_streak(self) -> int:
        """
        Calculate the current streak of completed periods.
        
        Returns:
            int: Number of consecutive periods the habit was completed
        """
        if not self.completions:
            return 0
        
        # Sort completions by date
        sorted_completions = sorted(self.completions)
        latest_completion = sorted_completions[-1].date()
        
        # Start checking from the most recent completion
        current_date = datetime.now().date()
        
        # If the latest completion is not from today (daily) or this week (weekly),
        # then the streak is already broken
        if self.periodicity == 'daily':
            if latest_completion < current_date:
                return 0
        else:  # weekly
            current_week_start = current_date - timedelta(days=current_date.weekday())
            if latest_completion < current_week_start:
                return 0
        
        streak = 0
        
        if self.periodicity == 'daily':
            # Check backwards day by day
            check_date = current_date
            while check_date >= self.created_at.date():
                if self.is_task_completed_for_period(datetime.combine(check_date, datetime.min.time())):
                    streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break
        else:  # weekly
            # Check backwards week by week
            check_date = current_week_start
            while check_date >= self.created_at.date():
                if self.is_task_completed_for_period(datetime.combine(check_date, datetime.min.time())):
                    streak += 1
                    check_date -= timedelta(days=7)
                else:
                    break
        
        return streak
    
    def get_longest_streak(self) -> int:
        """
        Calculate the longest streak of completed periods.
        
        Returns:
            int: Length of the longest streak
        """
        if not self.completions:
            return 0
        
        # Get all dates to check from creation to now
        current_date = datetime.now().date()
        created_date = self.created_at.date()
        
        all_periods = []
        if self.periodicity == 'daily':
            # Generate all days from creation to now
            days_count = (current_date - created_date).days + 1
            all_periods = [created_date + timedelta(days=i) for i in range(days_count)]
        else:  # weekly
            # Generate all weeks from creation to now
            first_week_start = created_date - timedelta(days=created_date.weekday())
            current_week_start = current_date - timedelta(days=current_date.weekday())
            weeks_count = ((current_week_start - first_week_start).days // 7) + 1
            all_periods = [first_week_start + timedelta(days=i*7) for i in range(weeks_count)]
        
        # Convert periods to completed/not completed status
        completion_status = [
            self.is_task_completed_for_period(datetime.combine(period, datetime.min.time()))
            for period in all_periods
        ]
        
        # Calculate longest streak from completion status
        longest_streak = 0
        current_streak = 0
        
        for status in completion_status:
            if status:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 0
        
        return longest_streak
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the habit to a dictionary representation.
        
        Returns:
            Dict: Dictionary representation of the habit
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'periodicity': self.periodicity,
            'created_at': self.created_at.isoformat(),
            'completions': [c.isoformat() for c in self.completions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Habit':
        """
        Create a Habit instance from a dictionary.
        
        Args:
            data: Dictionary representation of a habit
            
        Returns:
            Habit: New Habit instance
        """
        return cls(
            name=data['name'],
            description=data['description'],
            periodicity=data['periodicity'],
            id=data['id'],
            created_at=datetime.fromisoformat(data['created_at']),
            completions=[datetime.fromisoformat(c) for c in data['completions']]
        )


class HabitTracker:
    """
    Main class for managing habits.
    
    Attributes:
        habits (List[Habit]): List of habits being tracked
    """
    
    def __init__(self):
        """Initialize a new HabitTracker instance."""
        self.habits = []
        self.data_manager = DataManager()
        self.load_habits()
    
    def add_habit(self, habit: Habit) -> None:
        """
        Add a new habit to track.
        
        Args:
            habit: The habit to add
        """
        self.habits.append(habit)
        self.save_habits()
    
    def remove_habit(self, habit_id: str) -> bool:
        """
        Remove a habit by ID.
        
        Args:
            habit_id: ID of the habit to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        initial_count = len(self.habits)
        self.habits = [h for h in self.habits if h.id != habit_id]
        
        if len(self.habits) < initial_count:
            self.save_habits()
            return True
        return False
    
    def get_habit_by_id(self, habit_id: str) -> Optional[Habit]:
        """
        Get a habit by its ID.
        
        Args:
            habit_id: ID of the habit to find
            
        Returns:
            Optional[Habit]: The habit if found, None otherwise
        """
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        return None
    
    def complete_habit(self, habit_id: str) -> bool:
        """
        Mark a habit as completed for the current time.
        
        Args:
            habit_id: ID of the habit to complete
            
        Returns:
            bool: True if completed, False if habit not found
        """
        habit = self.get_habit_by_id(habit_id)
        if habit:
            habit.complete_task()
            self.save_habits()
            return True
        return False
    
    def load_habits(self) -> None:
        """Load habits from the data manager."""
        self.habits = self.data_manager.load_data()
    
    def save_habits(self) -> None:
        """Save habits using the data manager."""
        self.data_manager.save_data(self.habits)


class DataManager:
    """
    Class responsible for persisting and loading habit data.
    """
    
    def __init__(self):
        """Initialize the DataManager and ensure database is set up."""
        init_db()
    
    def save_data(self, habits: List[Habit]) -> None:
        """
        Save habits to the database.
        
        Args:
            habits: List of habits to save
        """
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM completions")
        cursor.execute("DELETE FROM habits")
        
        # Insert habits
        for habit in habits:
            cursor.execute(
                "INSERT INTO habits (id, name, description, periodicity, created_at) VALUES (?, ?, ?, ?, ?)",
                (habit.id, habit.name, habit.description, habit.periodicity, habit.created_at.isoformat())
            )
            
            # Insert completions
            for completion in habit.completions:
                completion_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO completions (id, habit_id, completed_at) VALUES (?, ?, ?)",
                    (completion_id, habit.id, completion.isoformat())
                )
        
        conn.commit()
        conn.close()
    
    def load_data(self) -> List[Habit]:
        """
        Load habits from the database.
        
        Returns:
            List[Habit]: List of loaded habits
        """
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        # Get all habits
        cursor.execute("SELECT * FROM habits")
        habit_rows = cursor.fetchall()
        
        habits = []
        for habit_row in habit_rows:
            # Get completions for this habit
            cursor.execute(
                "SELECT completed_at FROM completions WHERE habit_id = ?",
                (habit_row['id'],)
            )
            completion_rows = cursor.fetchall()
            completions = [datetime.fromisoformat(row['completed_at']) for row in completion_rows]
            
            # Create habit
            habit = Habit(
                id=habit_row['id'],
                name=habit_row['name'],
                description=habit_row['description'],
                periodicity=habit_row['periodicity'],
                created_at=datetime.fromisoformat(habit_row['created_at']),
                completions=completions
            )
            
            habits.append(habit)
        
        conn.close()
        return habits


# ========== Analytics Module ==========
# Using functional programming paradigm

def get_all_habits(habits: List[Habit]) -> List[Habit]:
    """
    Get all habits.
    
    Args:
        habits: List of habits to filter
        
    Returns:
        List[Habit]: All habits
    """
    return habits

def get_habits_by_periodicity(habits: List[Habit], periodicity: str) -> List[Habit]:
    """
    Filter habits by periodicity.
    
    Args:
        habits: List of habits to filter
        periodicity: Periodicity to filter by ('daily' or 'weekly')
        
    Returns:
        List[Habit]: Filtered habits
    """
    return list(filter(lambda habit: habit.periodicity == periodicity, habits))

def get_longest_streak_all(habits: List[Habit]) -> Tuple[Habit, int]:
    """
    Get the habit with the longest streak.
    
    Args:
        habits: List of habits to analyze
        
    Returns:
        Tuple[Habit, int]: Habit with longest streak and the streak length
    """
    if not habits:
        return None, 0
    
    # Map habits to (habit, streak) tuples
    habit_streaks = map(lambda habit: (habit, habit.get_longest_streak()), habits)
    
    # Find the maximum streak
    return max(habit_streaks, key=lambda x: x[1], default=(None, 0))

def get_longest_streak_for_habit(habit_id: str, habits: List[Habit]) -> int:
    """
    Get the longest streak for a specific habit.
    
    Args:
        habit_id: ID of the habit to check
        habits: List of habits to search through
        
    Returns:
        int: Longest streak
    """
    # Find the habit
    matching_habits = list(filter(lambda habit: habit.id == habit_id, habits))
    
    if not matching_habits:
        return 0
    
    return matching_habits[0].get_longest_streak()

def get_current_streak_for_habit(habit_id: str, habits: List[Habit]) -> int:
    """
    Get the current streak for a specific habit.
    
    Args:
        habit_id: ID of the habit to check
        habits: List of habits to search through
        
    Returns:
        int: Current streak
    """
    # Find the habit
    matching_habits = list(filter(lambda habit: habit.id == habit_id, habits))
    
    if not matching_habits:
        return 0
    
    return matching_habits[0].get_current_streak()

def get_habits_with_streak_info(habits: List[Habit]) -> List[Dict[str, Any]]:
    """
    Get all habits with their streak information.
    
    Args:
        habits: List of habits to analyze
        
    Returns:
        List[Dict]: List of habits with streak info
    """
    return list(map(
        lambda habit: {
            'id': habit.id,
            'name': habit.name,
            'periodicity': habit.periodicity,
            'current_streak': habit.get_current_streak(),
            'longest_streak': habit.get_longest_streak()
        },
        habits
    ))

def get_struggling_habits(habits: List[Habit], days: int = 30) -> List[Habit]:
    """
    Get habits that the user has struggled with recently.
    
    A habit is considered "struggling" if it has been broken more than
    completed in the given time period.
    
    Args:
        habits: List of habits to analyze
        days: Number of days to look back
        
    Returns:
        List[Habit]: List of struggling habits
    """
    # Get today's date
    today = datetime.now().date()
    
    # Calculate the start date for the analysis period
    start_date = today - timedelta(days=days)
    
    def is_struggling(habit: Habit) -> bool:
        # Count completed and broken periods in the time frame
        completed_periods = 0
        broken_periods = 0
        
        # Generate periods to check
        check_dates = []
        if habit.periodicity == 'daily':
            # Generate all days in the time period
            for i in range(days):
                check_date = today - timedelta(days=i)
                if check_date >= habit.created_at.date():
                    check_dates.append(check_date)
        else:  # weekly
            # Generate all weeks in the time period
            current_week_start = today - timedelta(days=today.weekday())
            weeks_to_check = (days // 7) + 1
            for i in range(weeks_to_check):
                check_date = current_week_start - timedelta(days=i*7)
                if check_date >= habit.created_at.date():
                    check_dates.append(check_date)
        
        # Count completed and broken periods
        for date in check_dates:
            if habit.is_task_completed_for_period(datetime.combine(date, datetime.min.time())):
                completed_periods += 1
            else:
                broken_periods += 1
        
        # A habit is struggling if broken more than completed
        return broken_periods > completed_periods and (broken_periods + completed_periods) > 0
    
    # Filter habits that are struggling
    return list(filter(is_struggling, habits))


# ========== Command-Line Interface ==========

@click.group()
def cli():
    """Habit Tracker: Track and analyze your habits."""
    pass

@cli.command()
@click.option('--name', prompt='Habit name', help='Name of the habit')
@click.option('--description', prompt='Description', help='Description of the habit')
@click.option('--periodicity', prompt='Periodicity (daily/weekly)', 
              type=click.Choice(['daily', 'weekly']), help='Frequency of the habit')
def add(name, description, periodicity):
    """Add a new habit to track."""
    tracker = HabitTracker()
    habit = Habit(name=name, description=description, periodicity=periodicity)
    tracker.add_habit(habit)
    click.echo(f"Habit '{name}' added successfully!")

@cli.command()
def list():
    """List all habits."""
    tracker = HabitTracker()
    habits = tracker.habits
    
    if not habits:
        click.echo("No habits found. Add some with the 'add' command.")
        return
    
    click.echo("\nYour Habits:")
    click.echo("=" * 50)
    
    for i, habit in enumerate(habits, 1):
        current_streak = habit.get_current_streak()
        click.echo(f"{i}. {habit.name} ({habit.periodicity})")
        click.echo(f"   Description: {habit.description}")
        click.echo(f"   Current streak: {current_streak} {habit.periodicity} period(s)")
        click.echo(f"   Created: {habit.created_at.strftime('%Y-%m-%d')}")
        click.echo(f"   ID: {habit.id}")
        click.echo("-" * 50)

@cli.command()
def complete():
    """Mark a habit as completed."""
    tracker = HabitTracker()
    habits = tracker.habits
    
    if not habits:
        click.echo("No habits found. Add some with the 'add' command.")
        return
    
    click.echo("\nSelect a habit to complete:")
    for i, habit in enumerate(habits, 1):
        click.echo(f"{i}. {habit.name} ({habit.periodicity})")
    
    choice = click.prompt("Enter the number of the habit to complete", type=int)
    
    if 1 <= choice <= len(habits):
        habit = habits[choice - 1]
        tracker.complete_habit(habit.id)
        click.echo(f"Habit '{habit.name}' marked as completed!")
        
        # Show updated streak
        current_streak = habit.get_current_streak()
        click.echo(f"Current streak: {current_streak} {habit.periodicity} period(s)!")
    else:
        click.echo("Invalid choice.")

@cli.command()
def remove():
    """Remove a habit."""
    tracker = HabitTracker()
    habits = tracker.habits
    
    if not habits:
        click.echo("No habits found. Add some with the 'add' command.")
        return
    
    click.echo("\nSelect a habit to remove:")
    for i, habit in enumerate(habits, 1):
        click.echo(f"{i}. {habit.name} ({habit.periodicity})")
    
    choice = click.prompt("Enter the number of the habit to remove", type=int)
    
    if 1 <= choice <= len(habits):
        habit = habits[choice - 1]
        confirmation = click.confirm(f"Are you sure you want to remove '{habit.name}'?")
        
        if confirmation:
            tracker.remove_habit(habit.id)
            click.echo(f"Habit '{habit.name}' removed.")
        else:
            click.echo("Operation cancelled.")
    else:
        click.echo("Invalid choice.")

@cli.command()
@click.option('--periodicity', type=click.Choice(['all', 'daily', 'weekly']), 
              default='all', help='Filter habits by periodicity')
def analyze(periodicity):
    """Analyze your habits."""
    tracker = HabitTracker()
    habits = tracker.habits
    
    if not habits:
        click.echo("No habits found. Add some with the 'add' command.")
        return
    
    click.echo("\nHabit Analysis:")
    click.echo("=" * 50)
    
    # Filter by periodicity if needed
    if periodicity != 'all':
        filtered_habits = get_habits_by_periodicity(habits, periodicity)
        if filtered_habits:
            click.echo(f"\n{periodicity.capitalize()} habits:")
            for habit in filtered_habits:
                click.echo(f"- {habit.name}")
        else:
            click.echo(f"No {periodicity} habits found.")
    
    # Show longest streak across all habits
    longest_streak_habit, longest_streak = get_longest_streak_all(habits)
    if longest_streak_habit:
        click.echo(f"\nLongest streak: {longest_streak} {longest_streak_habit.periodicity} period(s)")
        click.echo(f"Habit: {longest_streak_habit.name}")
    
    # Show all habits with their streaks
    click.echo("\nCurrent streaks:")
    streak_info = get_habits_with_streak_info(habits)
    for info in streak_info:
        click.echo(f"- {info['name']}: {info['current_streak']} {info['periodicity']} period(s)")
    
    # Show struggling habits
    struggling = get_struggling_habits(habits)
    if struggling:
        click.echo("\nHabits you've been struggling with:")
        for habit in struggling:
            click.echo(f"- {habit.name} ({habit.periodicity})")
    else:
        click.echo("\nYou're doing well with all your habits!")

@cli.command()
def reset_db():
    """Reset the database (for testing purposes)."""
    if click.confirm("Are you sure you want to reset the database? All habits will be lost."):
        # Remove the database file
        try:
            os.remove(get_db_path())
            click.echo("Database reset successfully.")
        except FileNotFoundError:
            click.echo("Database does not exist yet.")
        
        # Reinitialize the database
        init_db()

@cli.command()
def initialize():
    """Initialize the tracker with predefined habits and sample data."""
    if click.confirm("This will create 5 predefined habits with sample data. Continue?"):
        tracker = HabitTracker()
        
        # Check if habits already exist
        if tracker.habits:
            if not click.confirm("Habits already exist. Do you want to replace them?"):
                click.echo("Operation cancelled.")
                return
        
        # Create predefined habits
        habits = [
            Habit(
                name="Morning Exercise",
                description="30 minutes of physical activity",
                periodicity="daily",
                created_at=datetime.now() - timedelta(days=28)
            ),
            Habit(
                name="Read Book",
                description="Read for 20 minutes",
                periodicity="daily",
                created_at=datetime.now() - timedelta(days=28)
            ),
            Habit(
                name="Weekly Planning",
                description="Plan the upcoming week",
                periodicity="weekly",
                created_at=datetime.now() - timedelta(days=28)
            ),
            Habit(
                name="Grocery Shopping",
                description="Buy groceries for the week",
                periodicity="weekly",
                created_at=datetime.now() - timedelta(days=28)
            ),
            Habit(
                name="Practice Coding",
                description="Work on programming skills",
                periodicity="daily",
                created_at=datetime.now() - timedelta(days=28)
            )
        ]
        
        # Clear existing habits
        tracker.habits = []
        
        # Add sample completions for 4 weeks
        for habit in habits:
            # Generate random completions based on periodicity
            if habit.periodicity == 'daily':
                # For daily habits, complete on most days with some gaps
                for day in range(28):
                    # Skip some days randomly to create realistic data
                    if day % 4 != 0:  # Skip every 4th day
                        completion_date = habit.created_at + timedelta(days=day)
                        habit.completions.append(completion_date)
            else:  # weekly
                # For weekly habits, complete each week
                for week in range(4):
                    # Complete the habit on a random day of each week
                    week_start = habit.created_at + timedelta(days=week*7)
                    day_offset = (week % 3) + 1  # Different day each week
                    completion_date = week_start + timedelta(days=day_offset)
                    habit.completions.append(completion_date)
            
            tracker.add_habit(habit)
        
        click.echo("Predefined habits with sample data have been created!")

# Main entry point
if __name__ == '__main__':
    cli()
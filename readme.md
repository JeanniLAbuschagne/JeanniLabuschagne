# Habit Tracker

A command-line habit tracking application built with Python. This application helps you create and maintain good habits by tracking your progress and providing insightful analytics.

## Features

- Create and manage daily and weekly habits
- Mark habits as completed
- Track habit streaks (consecutive periods of completion)
- Analyze habits using various metrics
- Persist habit data between sessions using SQLite

## Installation

### Prerequisites

- Python 3.7 or later
- pip (Python package installer)

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/JeanniLAbuschagne/JeanniLabuschagne.git
   cd habit-tracker
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```
   pip install -e .
   ```

## Usage

The habit tracker provides a command-line interface with several commands:

### Initialize with Sample Data

To get started quickly with predefined habits and sample data:

```
habit-tracker initialize
```

This creates 5 predefined habits with 4 weeks of sample data.

### Add a New Habit

```
habit-tracker add
```

You'll be prompted to enter:
- Habit name
- Description
- Periodicity (daily or weekly)

### List All Habits

```
habit-tracker list
```

Displays all your habits with their current streaks.

### Complete a Habit

```
habit-tracker complete
```

Shows a list of your habits and allows you to mark one as completed for the current period.

### Analyze Habits

```
habit-tracker analyze
```

Shows analytics about your habits, including:
- Longest streak across all habits
- Current streaks for each habit
- Habits you've been struggling with recently

You can filter by periodicity:

```
habit-tracker analyze --periodicity daily
habit-tracker analyze --periodicity weekly
```

### Remove a Habit

```
habit-tracker remove
```

Lets you select and remove a habit from the tracker.

## Data Storage

Habit data is stored in a SQLite database located at:
- Windows: `C:\Users\<username>\.habit_tracker\habits.db`
- macOS/Linux: `~/.habit_tracker/habits.db`

## Testing

Run the test suite to verify the application is working correctly:

```
pytest
```

Or for more verbose output:

```
pytest -v
```

## Project Structure

- `habit_tracker.py`: Main module containing the application code
- `test_habit_tracker.py`: Test suite
- `setup.py`: Package setup file
- `requirements.txt`: Required dependencies

## Design Principles

This application uses:
- **Object-Oriented Programming** for habit management and data persistence
- **Functional Programming** for the analytics module
- **Command Pattern** for the CLI interface
- **Repository Pattern** for data access

## About Habit Tracking

### What is a Habit?

A habit is a clearly defined task that must be completed periodically. Examples include:
- Exercise for 30 minutes (daily)
- Read for 20 minutes (daily)
- Plan the upcoming week (weekly)
- Call a friend (weekly)

### What is a Streak?

A streak is the number of consecutive periods a habit has been maintained without breaking. For example, if you exercise every day for two weeks, you establish a 14-day streak.

### Breaking a Habit

A habit is considered "broken" if you miss completing it during the specified period (day or week).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

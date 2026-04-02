# 1 Subtract five days from current date
from datetime import datetime, timedelta

current_date = datetime.now()
new_date = current_date - timedelta(days=5)

print("Current date:", current_date)
print("Five days ago:", new_date)



# 2 Print yesterday, today, tomorrow
from datetime import datetime, timedelta

today = datetime.now().date()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)

print("Yesterday:", yesterday)
print("Today:", today)
print("Tomorrow:", tomorrow)



# 3 Drop microseconds from datetime
from datetime import datetime

now = datetime.now()
without_microseconds = now.replace(microsecond=0)

print("With microseconds:", now)
print("Without microseconds:", without_microseconds)



# 4 Calculate difference between two dates in seconds
from datetime import datetime

date1 = datetime(2025, 1, 1, 12, 0, 0)
date2 = datetime(2025, 1, 2, 12, 0, 0)

difference = date2 - date1
seconds = difference.total_seconds()

print("Difference in seconds:", seconds)
from datetime import datetime, timedelta
from typing import List, Dict, Any

def parse_time_blocks(time_block_data: List[Dict[str, Any]]) -> List[Any]:
    """
    Parse time block data from various formats
    """
    # This would be implemented based on your specific data format
    # Placeholder implementation
    return []

def calculate_time_difference(start_time: datetime, end_time: datetime) -> timedelta:
    """
    Calculate difference between two datetime objects
    """
    return end_time - start_time

def format_duration(minutes: int) -> str:
    """
    Format minutes into a human-readable string
    """
    if minutes >= 60:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes > 0:
            return f"{hours}h {remaining_minutes}m"
        else:
            return f"{hours}h"
    else:
        return f"{minutes}m"

def is_time_within_range(check_time: datetime, start_time: datetime, 
                        end_time: datetime) -> bool:
    """
    Check if a time is within a given range
    """
    return start_time <= check_time <= end_time

def find_available_time_slots(busy_slots: List[Dict[str, datetime]], 
                             day_start: datetime, day_end: datetime, 
                             min_duration: int) -> List[Dict[str, datetime]]:
    """
    Find available time slots between busy slots (min_duration in minutes)
    """
    available_slots = []
    min_timedelta = timedelta(minutes=min_duration)
    
    # Sort busy slots by start time
    busy_slots.sort(key=lambda x: x['start'])
    
    # Check before first busy slot
    first_busy = busy_slots[0] if busy_slots else None
    if first_busy and (first_busy['start'] - day_start) >= min_timedelta:
        available_slots.append({
            'start': day_start,
            'end': first_busy['start']
        })
    
    # Check between busy slots
    for i in range(len(busy_slots) - 1):
        current_end = busy_slots[i]['end']
        next_start = busy_slots[i + 1]['start']
        
        if (next_start - current_end) >= min_timedelta:
            available_slots.append({
                'start': current_end,
                'end': next_start
            })
    
    # Check after last busy slot
    if busy_slots:
        last_busy = busy_slots[-1]
        if (day_end - last_busy['end']) >= min_timedelta:
            available_slots.append({
                'start': last_busy['end'],
                'end': day_end
            })
    else:
        # No busy slots, entire day is available
        available_slots.append({
            'start': day_start,
            'end': day_end
        })
    
    return available_slots
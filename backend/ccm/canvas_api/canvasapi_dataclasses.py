from dataclasses import dataclass


@dataclass
class Section:
    id: int
    name: str
    course_id: int
    nonxlist_course_id: int
    total_students: int = 0
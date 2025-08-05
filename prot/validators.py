from dataclasses import dataclass


@dataclass
class GradeAssignmentPostModel:
    user_id: str
    submission_id: str
    assignment_id: str

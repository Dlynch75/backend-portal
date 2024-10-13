from school.models import JobPosting
from teacher.models import Hire

card_code = {
    0: "TJA",
    1: "TJR",
    2: "TJP",
    3: "TPA",
 }

def get_teacher_dashboard_cards(teacher):
    if teacher.is_teacher:
        total_jobs_applied = Hire.objects.filter(teacher=teacher).count()
        total_jobs_rejected = Hire.objects.filter(teacher=teacher, status="rejected").count()

        return [
            {
                "title": "Total Jobs Applied",
                "count": total_jobs_applied,
                "code": card_code[0]
            },
            {
                "title": "Total Jobs Rejected",
                "count": total_jobs_rejected,
                "code": card_code[1]
            }
        ]
    else:
        raise Exception("Login as Teacher")
    
def get_school_dashboard_cards(school):
    if school.is_school:
        # Logic for fetching school statistics
        total_jobs = JobPosting.objects.filter(school=school).count()
        total_applied_people = Hire.objects.filter(school=school).count()
        return [
            {
                "title": "Total Jobs Posted",
                "count": total_jobs,
                "code": card_code[2]
            },
            {
                "title": "Total People Applied",
                "count": total_applied_people,
                "code": card_code[3]
            }
        ]
    else:
        raise Exception("Login as School")
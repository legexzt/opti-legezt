from typing import List, Dict, Any

class PerformanceClassifier:
    """
    Classifies students into 3 tiers:
    1. Advanced Learners (Top Performers, High CGPA/CIE Marks, Zero Backlogs)
    2. Average / Moderate Learners (Consistent Performers)
    3. Slow / Weak Learners (Low Scores, Backlogs, Needs Remedial Attention)
    """

    DEFAULT_THRESHOLDS = {
        "advanced_cgpa_min": 7.5,
        "advanced_cie_min": 15.0,
        "slow_cgpa_max": 6.0,
        "slow_cie_max": 10.0,
        "slow_allow_backlogs": False, # If true, backlogs automatically mark as slow
        "advanced_max_backlogs": 0
    }

    @staticmethod
    def classify_students(students: List[Dict[str, Any]], thresholds: Dict[str, Any] = None) -> Dict[str, Any]:
        cfg = {**PerformanceClassifier.DEFAULT_THRESHOLDS, **(thresholds or {})}
        
        advanced_list = []
        average_list = []
        slow_list = []

        for student in students:
            # Check user override first
            user_override = student.get("category_override")
            if user_override:
                cat = user_override.lower()
                if "adv" in cat:
                    student["tier"] = "Advanced"
                    student["tier_code"] = "advanced"
                    advanced_list.append(student)
                    continue
                elif "slow" in cat or "weak" in cat:
                    student["tier"] = "Slow"
                    student["tier_code"] = "slow"
                    slow_list.append(student)
                    continue
                elif "avg" in cat or "mod" in cat:
                    student["tier"] = "Average"
                    student["tier_code"] = "average"
                    average_list.append(student)
                    continue

            cgpa = student.get("cgpa")
            sgpa = student.get("sgpa")
            cie = student.get("cie_marks")
            backlogs = student.get("backlog_count", 0)

            score_val = cgpa if cgpa is not None else sgpa
            
            # Classification rules
            is_advanced = False
            is_slow = False

            # Rule 1: Backlogs presence
            if backlogs > 0:
                is_slow = True
            
            # Rule 2: Based on CGPA / SGPA
            if score_val is not None and not is_slow:
                if score_val >= float(cfg["advanced_cgpa_min"]) and backlogs <= int(cfg["advanced_max_backlogs"]):
                    is_advanced = True
                elif score_val < float(cfg["slow_cgpa_max"]):
                    is_slow = True

            # Rule 3: Based on CIE Marks (if no CGPA or as supplementary metric)
            if cie is not None:
                if not is_slow and not is_advanced:
                    if cie >= float(cfg["advanced_cie_min"]) and backlogs == 0:
                        is_advanced = True
                    elif cie < float(cfg["slow_cie_max"]):
                        is_slow = True
                elif is_advanced and cie < float(cfg["slow_cie_max"]):
                    # Conflict: high cgpa but failed current mid exam -> categorized as average or slow
                    is_advanced = False
                    is_average = True

            if is_advanced:
                student["tier"] = "Advanced"
                student["tier_code"] = "advanced"
                if not student.get("action_plan") or "Remedial" in student.get("action_plan", ""):
                    student["action_plan"] = "Special guidance for competitive exams, NPTEL courses, hackathons, and research projects"
                if not student.get("observation_remarks"):
                    student["observation_remarks"] = "Active participation, quick grasp of concepts, high attendance"
                advanced_list.append(student)
            elif is_slow:
                student["tier"] = "Slow"
                student["tier_code"] = "slow"
                if not student.get("action_plan") or "hackathon" in student.get("action_plan", "").lower():
                    student["action_plan"] = "Remedial classes, simplified study notes, question bank practice, and 1-on-1 peer mentoring"
                if not student.get("observation_remarks"):
                    student["observation_remarks"] = "Needs conceptual clarity, regular revision, and guided practice"
                slow_list.append(student)
            else:
                student["tier"] = "Average"
                student["tier_code"] = "average"
                if not student.get("action_plan"):
                    student["action_plan"] = "Regular assignments, weekly tutorial practice, and group discussions"
                if not student.get("observation_remarks"):
                    student["observation_remarks"] = "Consistent attendance, satisfactory homework completion"
                average_list.append(student)

        # Re-number S.No for categorized lists
        for i, s in enumerate(advanced_list):
            s["advanced_s_no"] = i + 1
        for i, s in enumerate(slow_list):
            s["slow_s_no"] = i + 1
        for i, s in enumerate(average_list):
            s["average_s_no"] = i + 1

        total = len(students)
        stats = {
            "total_count": total,
            "advanced_count": len(advanced_list),
            "average_count": len(average_list),
            "slow_count": len(slow_list),
            "advanced_percentage": round((len(advanced_list) / total * 100), 1) if total > 0 else 0,
            "average_percentage": round((len(average_list) / total * 100), 1) if total > 0 else 0,
            "slow_percentage": round((len(slow_list) / total * 100), 1) if total > 0 else 0,
            "thresholds_used": cfg
        }

        return {
            "all_students": students,
            "advanced_learners": advanced_list,
            "average_learners": average_list,
            "slow_learners": slow_list,
            "statistics": stats
        }

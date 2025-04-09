class CourseParser:
    def __init__(self, driver):
        self.driver = driver

    def get_courses(self):
        courses = []
        # Navigate to the courses page
        self.driver.get("https://ecampus.smu.ac.kr/")
        # Logic to retrieve the list of courses goes here
        # This is a placeholder for actual implementation
        return courses

    def get_assignment_links(self):
        assignment_links = []
        # Logic to find all assignment links in the courses goes here
        # This is a placeholder for actual implementation
        return assignment_links

    def display_deadlines(self):
        assignments = self.get_assignment_links()
        for assignment in assignments:
            # Logic to extract and display deadlines goes here
            # This is a placeholder for actual implementation
            print(f"Assignment Link: {assignment['link']}, Due Date: {assignment['due_date']}")
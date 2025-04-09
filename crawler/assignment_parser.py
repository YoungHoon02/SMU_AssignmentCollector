class AssignmentParser:
    def __init__(self, driver):
        self.driver = driver

    def get_assignments(self, course_url):
        self.driver.get(course_url)
        assignment_links = self.driver.find_elements_by_xpath("//a[contains(@href, '/mod/assign/')]")
        assignments = []

        for link in assignment_links:
            title = link.text
            url = link.get_attribute('href')
            due_date = self.extract_due_date(link)
            assignments.append({
                'title': title,
                'link': url,
                'due_date': due_date
            })

        return assignments

    def extract_due_date(self, link):
        # Navigate to the assignment page to find the due date
        self.driver.get(link.get_attribute('href'))
        due_date_element = self.driver.find_element_by_xpath("//span[contains(text(), 'Due date:')]")
        due_date = due_date_element.text.split(': ')[1] if due_date_element else 'No due date found'
        return due_date
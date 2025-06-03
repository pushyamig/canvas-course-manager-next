DEFAUlT_CANVAS_SCOPES = [
    # Courses
    'url:GET|/api/v1/courses',
    'url:GET|/api/v1/courses/:id',
    'url:PUT|/api/v1/courses/:id',
    # Sections
    'url:GET|/api/v1/courses/:course_id/sections',
    'url:POST|/api/v1/courses/:course_id/sections',
    # Enrollments
    'url:GET|/api/v1/sections/:section_id/enrollments',
    # Accounts
    'url:GET|/api/v1/accounts',
    'url:GET|/api/v1/accounts/:account_id/courses',
]

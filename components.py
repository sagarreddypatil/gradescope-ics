import streamlit as st
from st_aggrid import AgGrid
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from st_aggrid import GridOptionsBuilder, GridUpdateMode, DataReturnMode, AgGridTheme
import aggrid_helper
import pandas as pd
from datetime import datetime, timezone, timedelta
import plotly.express as px
import matplotlib.pyplot as plt

from sources import get_courses, get_assignments, get_course_enrollments, get_submissions
from views import get_scores_in_rubric

from status_tests import is_overdue, is_near_due, is_submitted, now, date_format, is_below_mean, is_far_below_mean, is_far_above_mean


def display_hw_status(course_name:str, assign:pd.DataFrame, due_date: datetime, df: pd.DataFrame) -> None:
    """
    Outputs, for each assignment, the student status
    """
    st.markdown('### %s'%assign['name'])
    # st.write('released on %s and due on %s'%(assigned,due))
    st.write('Due on %s'%(due_date.strftime('%A, %B %d, %Y')))

    col1, col2 = st.tabs(['Students','Submissions by time'])

    by_time = df.copy().dropna()
    by_time['Submission Time'] = by_time['Submission Time'].apply(lambda x:pd.to_datetime(x, utc=True) if x else None)
    # by_time['Submission Time'] = by_time['Submission Time'].apply(lambda x: 
    #                                                                 datetime.datetime(x.year,x.month,x.day,0,0,0,0,tzinfo=timezone(offset=timedelta())) 
    #                                                                 if x.year > 0 else None)
    by_time = by_time.set_index(pd.DatetimeIndex(by_time['Submission Time']))

    # by_time = df.groupby('Submission Time').count().reset_index()
    by_time = by_time.groupby(pd.Grouper(freq='1D', label='right')).count()
    by_time = by_time[['Submission Time','Total Score']].rename(columns={'Submission Time': 'Day', 'Total Score':'Count'})
    with col2:
        # st.write("Submissions over time:")
        st.line_chart(data=by_time,x='Day',y='Count')

    late_df = df[df.apply(lambda x: is_overdue(x, due_date), axis=1)]['email']
    late_as_list = str(late_df.to_list())[1:-2].replace('\'','').replace(' ','')
    
    last_minute_df = df[df.apply(lambda x: is_near_due(x, due_date), axis=1)]['email']
    last_minute_as_list = str(last_minute_df.to_list())[1:-2].replace('\'','').replace(' ','')

    with col1:
        # st.write("Students and submissions:")
        st.dataframe(df.style.format(precision=0).apply(
            lambda x: [f"background-color:pink" 
                        if is_overdue(x, due_date) 
                        else f'background-color:mistyrose' 
                            if is_near_due(x, due_date) 
                            else 'background-color:lightgreen' if is_submitted(x) else '' for i in x],
            axis=1), use_container_width=True,hide_index=True,
                    column_config={
                        'name':None,'sid':None,'cid':None,
                        'gs_assignment_id':None,'Last Name':None,'First Name':None, 
                        'assigned':None,'due': None,
                        'shortname':None,
                        # 'Sections':None,
                        'gs_course_id': None,
                        'gs_user_id': None,
                        'gs_student_id': None,
                        'canvas_sid': None,
                        'canvas_course_id': None,
                        'sis_course_id': None,
                        'Total Score':st.column_config.NumberColumn(step=1,format="$%d"),
                        'Max Points':st.column_config.NumberColumn(step=1,format="$%d"),
                        # 'Submission Time':st.column_config.DatetimeColumn(format="D MM YY, h:mm a")
                        })
        
        if len(late_df) > 0:
            URL_STRING = "mailto:" + late_as_list + "?subject=Late homework&body=Hi, we have not received your submission for " + assign['name'] + " for " + course_name.strip() + ". Please let us know if you need special accommodation."

            st.markdown(
                f'<a href="{URL_STRING}" style="display: inline-block; padding: 12px 20px; background-color: #4CAF50; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 4px;">Email late students</a>',
                unsafe_allow_html=True
            )
        if len(last_minute_df) > 0:
            URL_STRING = "mailto:" + last_minute_as_list + "?subject=Approaching deadline&body=Hi, as a reminder, " + assign['name'] + " for " + course_name.strip() + " is nearly due. Please let us know if you need special accommodation."

            st.markdown(
                f'<a href="{URL_STRING}" style="display: inline-block; padding: 12px 20px; background-color: #4CAF50; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 4px;">Email reminder about deadline</a>',
                unsafe_allow_html=True
            )

def display_course(course_filter: pd.DataFrame):
    """
    Given a course dataframe (with a singleton row), displays for each assignment (in ascending order of deadline):
    - a line chart of submissions over time
    - a table of students, with color coding for overdue, near due, and submitted
    """

    courses_df = get_courses()
    enrollments = get_course_enrollments()
    assignments_df = get_assignments()

    course = courses_df[courses_df['shortname']==course_filter].iloc[0]
    # assigns = assignments_df[assignments_df['cid']==course['cid']].copy().dropna()
    st.subheader("Status of %s:"%course['shortname'])

    # col1, col2 = st.tabs(['Totals','Detailed'])

    grading_dfs = display_hw_progress(course)

    courses = []
    for course_sheet in grading_dfs:
        if len(course_sheet):
            courses.append(course_sheet.iloc[0]['canvas_sid'])

    tabs = st.tabs([str(int(x)) for x in courses])

    for inx, course in enumerate(courses):
        this_course = grading_dfs[inx]

        with tabs[inx]:
            assign_grades(this_course)

        #display_hw_totals(course)
        #display_hw_assignment_scores(course)


    # with col2:
    #     course_info = enrollments[enrollments['gs_course_id']==course['gs_course_id']]
    #     assigns = course_info[['gs_assignment_id','name']].drop_duplicates()
    #     # assigns['due'] = assigns['due'].apply(lambda x:pd.to_datetime(x) if x else None)
    #     # assigns = assigns.sort_values('due',ascending=True)

    #     for a,assign in assigns.iterrows():
    #         df = course_info[course_info['gs_assignment_id']==assign['gs_assignment_id']].\
    #             drop(columns=['gs_course_id','gs_assignment_id'])
            
    #         # assigned = list(df['assigned'].drop_duplicates())[0]
    #         due = list(df['due'].drop_duplicates())[0]
    #         # assigned_date = assigned#datetime.strptime(assigned, date_format)
    #         due_date = due#datetime.strptime(due, date_format)

    #         with st.container():
    #             # Skip homework if it's not yet due!
    #             if now < due_date:
    #                 continue

    #             display_hw_status(course['name'], assign, due_date, df)
    #     st.divider()

def display_birds_eye(birds_eye_df: pd.DataFrame) -> None:
    overdue = 0
    pending = 0
    birds_eye_df.style.apply(
                lambda x: [f"background-color:pink" 
                            if overdue >0
                            else f'background-color:mistyrose' 
                                if pending >0
                                else 'background-color:lightgreen' for i in x],
                axis=1)
    
    gb = GridOptionsBuilder.from_dataframe(birds_eye_df)
                
    #### Add hyperlinks
    # gb.configure_column(
    #     "Course",
    #     headerName="Course",
    #     width=100,
    #     cellRenderer=aggrid_helper.add_url('Course', '/#status-of-cis-5450-2023-fall-big-data-analytics-on-campus')
    # )
    other_options = {'suppressColumnVirtualisation': True}
    gb.configure_grid_options(**other_options)

    gridOptions = gb.build()
    gridOptions['getRowStyle'] = aggrid_helper.add_highlight('params.data["😅"] > 0 || params.data["😰"] > 0', 'black', 'mistyrose')

    st.write("Overall status:")
    grid = AgGrid(
        birds_eye_df,
        gridOptions=gridOptions,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        allow_unsafe_jscode=True
        )
    
def display_rubric_component(title: str, column: str, max_column: str, dataframe: pd.DataFrame) -> None:
    st.markdown('### %s'%title)
    if column and len(dataframe):
        mean = dataframe[column].dropna().mean()
        overall_max = dataframe[max_column].dropna().max()

        if not pd.isna(mean) and not pd.isna(overall_max):
            st.write('Mean: {:.2f}, Max: {}'.format(mean, overall_max))
        elif not pd.isna(mean):
            st.write('Mean: {:.2f}'.format(mean))
        elif not pd.isna(overall_max):
            st.write('Max: {}'.format(overall_max))
        st.dataframe(dataframe.style.format(precision=0).apply(
            lambda x: [f"background-color:pink" 
                        if is_far_below_mean(x, mean, column) 
                        else f'background-color:mistyrose' 
                            if is_below_mean(x, mean, column) 
                            else 'background-color:lightgreen' 
                                    if is_far_above_mean(x, overall_max, mean, column)
                                    else '' for i in x],
            axis=1), use_container_width=True,hide_index=True)
    else:
        st.dataframe(dataframe, use_container_width=True,hide_index=True)

def display_hw_assignment_scores(course = None) -> None:
    st.markdown('## Student Scores by Assignment')

    courses = get_courses()
    if course is not None:
        courses = courses[courses['cid'] == course['cid']]

    scores = get_submissions().\
        merge(get_assignments().rename(columns={'name': 'assignment'}), \
            left_on=['course_id','assign_id'], \
                right_on=['course_id','assignment_id']).\
                    merge(courses.drop(columns=['name','year']).rename(columns={'shortname':'course'}), \
                        left_on='course_id', right_on='cid')\
                            [[#'course', 
                              'First Name', 'Last Name', 'Email', 'assignment', 'Total Score', 'due', 'Status', 'Lateness (H:M:S)']].\
                            sort_values(by=['due', 'Last Name', 'First Name'])

        #melt(id_vars=['First Name', 'Last Name', 'Email', 'Sections', 'course_id', 'assign_id', 'Submission ID', 'Total Score', 'Max Points', 'Submission Time', 'Status', 'Lateness (H:M:S)']).\

    st.dataframe(scores)


def assign_grades(grade_totals: pd.DataFrame) -> None:
    thresholds = {'A+': 97, 'A': 93, 'A-': 90, 'B+': 87, 'B': 83, 'B-': 80, 'C+': 77, 'C': 73, 'C-': 70, 'D+': 67, 'D': 63, 'D-': 60, 'F': 0}

    prior = 100
    for grade in thresholds:
        thresholds[grade] = st.slider("Threshold for {}".format(grade), 0, prior, thresholds[grade])
        # prior = thresholds[grade]

    grade_totals['grade'] = ''
    ## This is taking advantage of Python's ordered dictionaries
    for grade in thresholds:
        # grade_totals[grade] = grade_totals['Total Score'].apply(lambda x: 1 if x >= thresholds[grade] else 0)
        # st.write("Assessing {} grades".format(grade))
        grade_totals['grade'] = grade_totals.apply\
            (lambda x: x['grade'] if not pd.isna(x['grade']) and len(x['grade']) > 0 \
             else grade if x['Total Points'] >= thresholds[grade] else '', axis=1)

    distrib = grade_totals.groupby('grade').count()['Total Points']#.reset_index()
    fig, ax = plt.subplots()
    plt.ylabel('Number of students')
    plt.xlabel("(Proposed) Letter Grade")
    plt.title("Grade distribution")

    for grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F']:
        if grade not in distrib:
            distrib[grade] = 0
    distrib = distrib[['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F']]
    bars = ax.bar(distrib.index, distrib)#['Total Points'])
    ax.bar_label(bars)
    fig.show()

    st.pyplot(fig)
    st.dataframe(grade_totals[['student','student_id','email','Total Points','grade']].sort_values(by=['Total Points','student']), use_container_width=True,hide_index=True)


def display_hw_totals(course = None) -> None:
    st.markdown('## Student Aggregate Status')

    courses = get_courses()
    if course is not None:
        courses = courses[courses['cid'] == course['cid']]

    scores = get_submissions().\
        merge(get_assignments().rename(columns={'name': 'assignment'}), \
            left_on=['course_id','assign_id'], \
                right_on=['course_id','assignment_id']).\
                    merge(courses.drop(columns=['name','year']).rename(columns={'shortname':'course'}), \
                        left_on='course_id', right_on='cid')\
                            [[#'course', 
                              'First Name', 'Last Name', 'Email', 'assignment', 'Total Score', 'due', 'Status', 'Lateness (H:M:S)']].\
                            groupby(by=['Email','Last Name','First Name']).sum()['Total Score'].reset_index().\
                            sort_values(by=['Total Score'])

        #melt(id_vars=['First Name', 'Last Name', 'Email', 'Sections', 'course_id', 'assign_id', 'Submission ID', 'Total Score', 'Max Points', 'Submission Time', 'Status', 'Lateness (H:M:S)']).\

    mean  = scores['Total Score'].mean()

    st.markdown('Out of {} students, the mean score is {} out of {}'.format(int(len(scores)), int(mean), int(scores['Total Score'].max())))

    st.dataframe(scores.style.format(precision=0).apply(
        lambda x: [f"background-color:pink" 
                    if is_far_below_mean(x, mean) 
                    else f'background-color:mistyrose' 
                        if is_below_mean(x, mean) 
                        else 'background-color:lightgreen' for i in x],
        axis=1), use_container_width=True,hide_index=True,
                column_config={
                    'name':None,'sid':None,'cid':None,
                    'assign_id':None,
                    'assigned':None,'due': None,
                    'shortname':None,
                    'Sections': None,
                    'gs_course_id': None,
                    'user_id': None,
                    'student_id': None,
                    'canvas_sid': None,
                    'canvas_id': None,
                    'sis_course_id': None,
                    'Total Score':st.column_config.NumberColumn(step=1,format="$%d")
                    # 'Submission Time':st.column_config.DatetimeColumn(format="D MM YY, h:mm a")
                    })


def display_hw_progress(course = None) -> list[pd.DataFrame]:
    return get_scores_in_rubric(display_rubric_component, course)

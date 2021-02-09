import pandas as pd
import seaborn as sns

# Definitions
"""df = pd.read_excel(
    "CCTC Wave 1 Dataset for Public Distribution.xlsx",
    sheet_name=1
)"""
df = pd.read_pickle('data/pickled_df')

metadata = {
    'categories': {
        'generation': 'agegen',
        'education': 'q40',
        'employment_status': 'q41',
        'income_bracket': 'q42',
        'self_id_PI': 'q39_1',
        'self_id_AA': 'q39_2',
        'self_id_NA': 'q39_3',
        'self_id_WC': 'q39_4',
        'state': 'StateName',
        'region_large': 'REGION4',
        'region_small': 'REGION9',
    },
}


# Analysis object
class Analysis:
    def __init__(
            self,
            job,
            df=df,
            metadata=metadata,
    ):
        self.categories = {
            key: metadata['categories'][key]
            for key in job['categories'] + list(job['filters'].keys())
        }
        self.columns = list(self.categories.values()) + list(job['questions'].keys())
        self.dataframes = {'df': df[self.columns]}
        self.job = job
        self.plots ={}
        self.filter_self()
        self.collect_answers()
        self.aggregate_answers()
        self.get_proportions_df()
        if 'sort_order' in job.keys():
            self.sort_proportions_melted_df()
        self.make_seaborn_barplot()


    def filter_self(self):
        _df = self.dataframes['df']
        for (category, values) in self.job['filters'].items():
            _df = _df[_df[self.categories[category]].isin(values)]
        self.dataframes['df'] = _df


    def collect_answers(self):
        _df = self.dataframes['df']
        if ('split_question' in list(self.job.keys())):
            for answer in self.job['questions'][self.job['split_question']]:
                _df[answer] = _df[self.job['split_question']].apply(lambda cell: True if str(cell) in answer else False)
        else:
            for (question, answers) in self.job['questions'].items():
                _df[question] = _df[question].apply(lambda cell: True if str(cell) in answers else False)
        self.dataframes['df'] = _df


    def aggregate_answers(self):
        _df = self.dataframes['df']
        if 'aggregation' in list(self.job.keys()):
            for (name, collection) in self.job['aggregation'].items():
                aggregate_df = pd.DataFrame(_df[collection])
                _df[name] = aggregate_df.any(axis=1)
        else:
            pass
        self.dataframes['df'] = _df


    def get_proportions_df(self, groups=None, group_by=None):
        _df = self.dataframes['df']
        aggregate = True if 'aggregation' in list(self.job.keys()) else False
        split = True if 'split_question' in list(self.job.keys()) else False
        if not group_by:
            group_by = self.job['categories'][0]
        if not groups:
            groups = set(_df[self.categories[group_by]])
        if aggregate:
            columns = self.job['aggregation'].keys()
        elif split:
            columns = self.job['questions'][self.job['split_question']]
        else:
            columns = self.job['questions'].keys()
        results = {'index': list(columns)}
        for group in groups:
            group_df = _df[_df[self.categories[group_by]] == group]
            proportions = []
            for column in columns:
                proportions.append(group_df[column].values.sum() / group_df.shape[0])
            results.update({group: proportions})
        self.df_metadata = {
            'categories': list(columns),
            'groups': list(groups),
        }
        self.dataframes.update({
            'proportions': pd.DataFrame(results),
            'proportions_melted': pd.melt(pd.DataFrame(results), id_vars=['index'])
        })


    def make_seaborn_barplot(self, palette="viridis", **kwargs):
        # if 'col' in kwargs:
        #     plot = sns.catplot(
        #         data=self.dataframes['proportions_melted'],
        #         hue='variable',
        #         palette=palette,
        #         x='index',
        #         y='value',
        #         **kwargs
        #     )
        # else:
        plot = sns.barplot(
            data=self.dataframes['proportions_melted'],
            hue='variable',
            palette=palette,
            x='index',
            y='value',
            **kwargs
        )
        if 'labels' in self.job:
            labels = self.job['labels']
            if 'title' in labels:
                plot.set_title(labels['title'])
            if 'xlabel' in labels:
                plot.set(xlabel=labels['xlabel'])
            if 'ylabel' in labels:
                plot.set(ylabel=labels['ylabel'])
        plot.legend(bbox_to_anchor=(1, 1), loc=2)
        self.plots.update({'seaborn_barplot': plot})

    def sort_proportions_melted_df(self, sort_order=[]):
        if 'sort_order' in self.job.keys():
            sort_order = self.job['sort_order']
        _df = self.dataframes['proportions_melted']
        df_list = []
        for item in sort_order:
            df_list.append(_df[_df['variable'] == item])
        self.dataframes['proportions_melted'] = pd.concat(df_list)

    def convert_qs_to_questions(self):
        self.dataframes['proportions_melted']['index'] = [self.job['questions'][q][0] for q in list(self.dataframes['proportions_melted']['index'])]


def column_values(question):
    columns = list(df.columns)
    values = [set(df[column]) for column in list(df.columns)]
    column_list = [match for match in columns if question in match and 'TEXT' not in match]
    for column in column_list:
        index = columns.index(column)
        print("{}: {}".format(columns[index], values[index]))


# Example job for testing
example_job = {
    'categories': [
        'income_bracket',
        'employment_status',
    ],
    'questions': {
        'q1_1': ['Socialized online or by phone'],
        'q1_2': ['Spent time outdoors'],
        'q1_3': ['Listened to music, or watched a musical performance online'],
    },
    'aggregation': {
        'agg_group_1': ['q1_1', 'q1_2'],
        'agg_group_2': ['q1_3'],
    },
    'filters': {
        'region_small': ['East North Central'],
    },
}

# Figure Settings
sns.set(rc={'figure.figsize':(24,16)})

# Analysis Plans
categories = [
    'generation',
    'income_bracket',
]

filters = {
    'region_small': ['East North Central'],
    'generation': [
        'Silent (1928-45)',
        'Gen Z (1997-2012)',
        'Boomers (1946-64)',
        'Gen X (1965-80)',
        'Millennials (1981-96)'
    ],
}

sort_order = ['Silent (1928-45)', 'Boomers (1946-64)', 'Gen X (1965-80)', 'Millennials (1981-96)', 'Gen Z (1997-2012)']

analysis_1 = Analysis({
    'aggregation': {
        'ArtMuseum': ['q7_1'],
        'FoodAndDrink': ['q7_17'],
        'Theater': ['q7_18', 'q7_19'],
        'Music': ['q7_21', 'q7_22', 'q7_23', 'q7_24', 'q7_25'],
        'Dance': ['q7_26', 'q7_27', 'q7_28'],
    },
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'Did you do any of the following activities last year (2019)?',
        'xlabel': 'Activity',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q7_1': ['Art museum'],
        'q7_17': ['Food and drink experience'],
        'q7_18': ['Play (non-musical)'],
        'q7_19': ['Musical'],
        'q7_21': ['Popular music'],
        'q7_22': ['Classical music'],
        'q7_23': ['Jazz music'],
        'q7_24': ['Opera'],
        'q7_25': ['World music'],
        'q7_26': ['Contemporary dance'],
        'q7_27': ['Ballet'],
        'q7_28': ['Regional dance'],
    },
    'sort_order': sort_order,
})
analysis_1.plots['seaborn_barplot'].get_figure().savefig('analysis_1', bbox_inches='tight')

analysis_2 = Analysis({
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'Still thinking back to 2019, about how often did you participate in those kinds of activities — the kind you think of as cultural?',
        'xlabel': 'Frequency',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q9': ['A few times a week', 'A few times a month', 'About once a month', 'A few times over the year'],
    },
    'sort_order': sort_order,
    'split_question': 'q9',
})
analysis_2.plots['seaborn_barplot'].get_figure().savefig('analysis_2', bbox_inches='tight')

analysis_3 = Analysis({
    'aggregation':{
        'Arts Org. Member': ['q34_1'],
        'Arts Org. Subscriber/Ticket-Holder': ['q34_2'],
        'Arts Org. Volunteer': ['q34_3'],
        'Arts Org. Employee': ['q34_4'],
        'Artist or Arts Educator': ['q34_5'],
        'None of These': ['q34_99'],
    },
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'During 2019 (before Covid-19), did any of these apply to you?',
        'xlabel': 'Question',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q34_1': ['I was a member of an arts or culture organization'],
        'q34_2': ['I was a subscriber or season-ticket holder to an arts and culture organization'],
        'q34_3': ['I volunteered at an arts or culture organization'],
        'q34_4': ['I was employed by an arts or culture organization'],
        'q34_5': ['I earned money as an artist or arts educator/ teaching artist'],
        'q34_99': ['None of these'],
    },
    'sort_order': sort_order,
})
analysis_3.plots['seaborn_barplot'].get_figure().savefig('analysis_3', bbox_inches='tight')


analysis_4 = Analysis({
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'During a crisis like Covid-19, how important or unimportant are arts & culture organizations to you?',
        'xlabel': '"Not Important at All" to "Extremely Important"',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {'q17': ['1', '2', '3', '4', '5']},
    'sort_order': sort_order,
    'split_question': 'q17',
})
analysis_4.plots['seaborn_barplot'].get_figure().savefig('analysis_4', bbox_inches='tight')


analysis_5 = Analysis({
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'Has your income changed because of Covid-19?',
        'xlabel': 'Income Impact',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q32': ['No, there has been no change to my income',
                'Yes, I have no income now',
                'Prefer not to answer',
                'Yes, I still have some income but less than before']
    },
    'sort_order': sort_order,
    'split_question': 'q32',
})
analysis_5.plots['seaborn_barplot'].get_figure().savefig('analysis_5', bbox_inches='tight')


analysis_6 = Analysis({
    'aggregation':{
        'Listened to music, or watched a musical performance online': ['q1_3'],
        'Watched a live-streaming event or performance': ['q1_7'],
        'Participated in a live interactive event online': ['q1_15'],
    },
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'Which of the following activities have you done in the past 30 days?',
        'xlabel': 'Activity',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q1_3': ['Listened to music, or watched a musical performance online'],
        'q1_7': ['Watched a live-streaming event or performance'],
        'q1_15': ['Participated in a live interactive event online'],
    },
    'sort_order': sort_order,
})
analysis_6.plots['seaborn_barplot'].get_figure().savefig('analysis_6', bbox_inches='tight')


analysis_7 = Analysis({
    'aggregation': {
        'Hope': ['q6_1'],
        'Humor': ['q6_2'],
        'Distraction': ['q6_3'],
        'Connection with other people': ['q6_4'],
        'Staying informed': ['q6_5'],
        'Getting outdoors': ['q6_6'],
        'Expressing myself creatively': ['q6_7'],
        'Being challenged': ['q6_8'],
        'Fun': ['q6_9'],
        'Feeling like I’m part of something': ['q6_10'],
    },
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'What do you want more of in your life right now?',
        'xlabel': 'Want More',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q6_1': ['Hope'],
        'q6_2': ['Humor'],
        'q6_3': ['Distraction'],
        'q6_4': ['Connection with other people'],
        'q6_5': ['Staying informed, with trusted information'],
        'q6_6': ['Getting outdoors'],
        'q6_7': ['Expressing myself creatively'],
        'q6_8': ['Being challenged'],
        'q6_9': ['Fun'],
        'q6_10': ['Feeling like I’m part of something'],
    },
    'sort_order': sort_order,
})
analysis_7.plots['seaborn_barplot'].get_figure().savefig('analysis_7', bbox_inches='tight')


analysis_8 = Analysis({
    'aggregation': {
        'a. I hope the arts & culture organizations\nin my area will change after the pandemic\nto be more relevant to people like me.': ['1'],
        'b. The arts & culture organizations in my\narea are really struggling financially\nbecause of Covid-19.': ['2'],
        'c. I’ve seen or heard about an arts or\ncultural organization in my area helping\nour community during the crisis in some\nspecific way.': ['3'],
        'd. During this crisis, we should support\nother kinds of nonprofit organizations in\nmy area before supporting arts & culture\norganizations.': ['4'],
        'e. I’m hearing a lot from arts & culture\norganizations during Covid-19, via emails,\nsocial media, etc.': ['5'],
        'f. I wish I were hearing more from arts\n& culture organizations during Covid-19,\nvia emails, social media, etc.': ['99'],
    },
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'Please tell us how much you personally agree or disagree with the following statements.',
        'xlabel': 'Question',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {'q19e': ['1', '2', '3', '4', '5', '99']},
    'sort_order': sort_order,
    'split_question': 'q19e',
})
analysis_8.plots['seaborn_barplot'].get_figure().savefig('analysis_8', bbox_inches='tight')


analysis_9 = Analysis({
    'aggregation': {
        'Materials or activities for kids': ['q12_4'],
        'Live-stream performances or events': ['q12_5'],
        'Interactive events': ['q12_6'],
        'Pre-recorded performances': ['q12_7'],
        'Classes, courses, or workshops': ['q12_9'],
        'Communit meetings or discussions': ['q12_10'],
    },
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'Have you done any of those online or digital cultural activities yourself in the past 30 days?',
        'xlabel': 'Activity',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q12_4': ['Online materials or activities for kids'],
        'q12_5': ['Live-stream performances or cultural events'],
        'q12_6': ['Interactive events online, where you can participate via chat, audio, or video'],
        'q12_7': ['Pre-recorded performances filmed before the shutdowns'],
        'q12_9': ['Online classes, courses, or workshops (from arts groups, zoos, etc.)'],
        'q12_10': ['Online community meetings or discussions (presented by artists, zoos, etc.)'],
    },
    'sort_order': sort_order,
})
analysis_9.plots['seaborn_barplot'].get_figure().savefig('analysis_9', bbox_inches='tight')


analysis_10 = Analysis({
    'aggregation': {
        'Pop, hip-hop, or rap music': ['q4_1'],
        'Country music': ['q4_2'],
        'Rock or alternative music': ['q4_3'],
        'Jazz music': ['q4_4'],
        'Folk music': ['q4_5'],
        'Musical theater/Broadway': ['q4_6'],
        'Live theater or drama': ['q4_7'],
        'Classical music': ['q4_11'],
        'Opera': ['q4_14'],
        'Ballet': ['q4_15'],
        'Contemporary dance': ['q4_16'],
    },
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'If you watched a special live-streaming event or performance in the past 30 days, what kind were they?',
        'xlabel': 'Event or Performance Type',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q4_1': ['Pop, hip-hop, or rap music'],
        'q4_2': ['Country music'],
        'q4_3': ['Rock or alternative music'],
        'q4_4': ['Jazz music'],
        'q4_5': ['Folk music'],
        'q4_6': ['Musical theater or Broadway'],
        'q4_7': ['Live theater or drama'],
        'q4_11': ['Classical music'],
        'q4_14': ['Opera'],
        'q4_15': ['Ballet'],
        'q4_16': ['Contemporary dance'],
    },
    'sort_order': sort_order,
})
analysis_10.plots['seaborn_barplot'].get_figure().savefig('analysis_10', bbox_inches='tight')


analysis_11 = Analysis({
    'aggregation': {
        'Friendlier to all kinds of people': ['q28_1'],
        'Less formal': ['q28_2'],
        'Stories or content that connect to my life': ['q28_3'],
        'More diverse voices and faces': ['q28_4'],
        'More focus on our local community': ['q28_5'],
        'More frequent new works or exhibits': ['q28_6'],
        'More fun': ['q28_7'],
        'Working with other nonprofits in our community': ['q28_8'],
        'Supporting local artists, organizers, etc.': ['q28_9'],
        'More child-friendly': ['q28_10'],
        'Engage more young people': ['q28_11'],
        'Treat their employees fairly and equitably': ['q28_12'],
        'Nothing — I wouldn’t change them at all': ['q28_99'],
    },
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'Which of the following factors will most influence your decision to resume attending in-person arts & culture experiences?',
        'xlabel': 'Factors',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q28_1': ['Friendlier to all kinds of people'],
        'q28_2': ['Less formal'],
        'q28_3': ['Stories or content that connect to my life'],
        'q28_4': ['More diverse voices and faces'],
        'q28_5': ['More focus on our local community'],
        'q28_6': ['More frequent new works or exhibits'],
        'q28_7': ['More fun'],
        'q28_8': ['Working with other nonprofits in our community'],
        'q28_9': ['Supporting local artists, organizers, etc.'],
        'q28_10': ['More child-friendly'],
        'q28_11': ['Engage more young people'],
        'q28_12': ['Treat their employees fairly and equitably'],
        'q28_99': ['Nothing — I wouldn’t change them at all'],
    },
    'sort_order': sort_order,
})
for item in analysis_11.plots['seaborn_barplot'].get_xticklabels():
    item.set_rotation(60)
analysis_11.plots['seaborn_barplot'].get_figure().savefig('analysis_11', bbox_inches='tight')


analysis_12 = Analysis({
    'aggregation': {
        'Before the pandemic': ['q23_12'],
        'During the pandemic': ['q24_12'],
    },
    'categories': categories,
    'filters': filters,
    'labels': {
        'title': 'Donated to Dance Organizations',
        'xlabel': 'When?',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q23_12': ['Dance group'],
        'q24_12': ['Dance group'],
    },
    'sort_order': sort_order,
})
analysis_12.plots['seaborn_barplot'].get_figure().savefig('analysis_12', bbox_inches='tight')

# Income by generation
Analysis({
    'categories': ['generation'],
    'filters': filters,
    'labels': {
        'title': 'Which of the following ranges describes your annual household income for 2019?',
        'xlabel': 'Income',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q42': [
            'Prefer not to answer',
            'Under $25,000',
            '$25,000–$49,999',
            '$50,000–$99,999',
            '$100,000–$149,999',
            '$150,000–$199,999',
            '$200,000 or more',
        ]
    },
    'sort_order': sort_order,
    'split_question': 'q42',
}).plots['seaborn_barplot'].get_figure().savefig('analysis_income', bbox_inches='tight')

# Participation
Analysis({
    'aggregation': {
        'ArtMuseum': ['q7_1'],
        'FoodAndDrink': ['q7_17'],
        'Theater': ['q7_18', 'q7_19'],
        'Music': ['q7_21', 'q7_22', 'q7_23', 'q7_24', 'q7_25'],
        'Dance': ['q7_26', 'q7_27', 'q7_28'],
    },
    'categories': categories,
    'filters': {
        'region_small': ['Middle Atlantic']
    },
    'labels': {
        'title': 'Did you do any of the following activities last year (2019)?',
        'xlabel': 'Activity',
        'ylabel': 'Proportion Responding Yes',
    },
    'questions': {
        'q7_1': ['Art museum'],
        'q7_17': ['Food and drink experience'],
        'q7_18': ['Play (non-musical)'],
        'q7_19': ['Musical'],
        'q7_21': ['Popular music'],
        'q7_22': ['Classical music'],
        'q7_23': ['Jazz music'],
        'q7_24': ['Opera'],
        'q7_25': ['World music'],
        'q7_26': ['Contemporary dance'],
        'q7_27': ['Ballet'],
        'q7_28': ['Regional dance'],
    },
    'sort_order': sort_order,
}).plots['seaborn_barplot'].get_figure().savefig('analysis_1a', bbox_inches='tight')

df[df['REGION9'] == 'East North Central'].shape
df[df['StateName'] == 'Indiana'].shape
df[df['CityName'] == 'Indianapolis'].shape

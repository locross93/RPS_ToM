import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

current_dir = os.path.dirname(__file__)  # Directory of the current script
file_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_per_episode.csv')

# Load the data
df_results = pd.read_csv(file_path)

# do not plot these tom agents - hm_gpt35
#df_results = df_results[~df_results['tom_agent_class'].str.contains('hm_gpt35')]

# Create the bar plot
plt.figure(figsize=(12, 6))
sns.barplot(x='sequential_agent_class', y='win_percentage', hue='tom_agent_class', data=df_results)
plt.title('Win Percentage by Sequential Agent and TOM Agent Classes')
plt.xlabel('Sequential Agent Class')
plt.ylabel('Win Percentage')
plt.legend(title='TOM Agent Class')
plt.xticks(rotation=45)
plt.tight_layout()
plt.ylim([0, 1])
plt.show()


combination_counts = df_results.groupby(['tom_agent_class', 'sequential_agent_class']).size()

# Print the counts
for (tom_agent, sequential_agent), count in combination_counts.items():
    print(f"tom_agent_class: {tom_agent}, sequential_agent_class: {sequential_agent}, count: {count}")
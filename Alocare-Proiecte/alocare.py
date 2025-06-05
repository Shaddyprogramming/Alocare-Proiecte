import pandas # library for data manipulation
import numpy # library for numerical operations
from numba import jit # JIT compiler for fast execution

SEED: int = 19032025 # Seed for random allocations
# the seed is the date of the challenge assigned, 19.03.2025
INPUT_PATH: str = 'data/lp3_proiecte_optiuni.csv' # Input CSV file path
OUTPUT_PATH: str = 'data/alocari_teme.csv' # Output CSV file path

@jit(cache=True, fastmath=True) # JIT compilation for performance optimization
def fast_random_choice(arr_size: int, seed_val: int) -> int:
   """
   Generate a random index within the range of the array size using a fixed seed.

   :param arr_size: Size of the array to choose from.
   :param seed_val: Seed value for reproducibility.
   :return: Random index within the array size.
   """
   numpy.random.seed(seed_val) # Set the random seed for reproducibility
   return numpy.random.randint(0, arr_size) # Generate a random index within the array size

def preprocess_dataframe(df: pandas.DataFrame) -> pandas.DataFrame:
    """
    Preprocess the input DataFrame to extract groups and domains from the 'Echipa' and 'Optiuni' columns.
    
    :param df: Input DataFrame containing 'Echipa' and 'Optiuni' columns.
    :return: Processed DataFrame with new columns for group, domains, and cleaned options.
    """
    df = df.copy() # Create a copy to avoid modifying the original DataFrame
    df['grupa'] = df['Echipa'].str.split('-', n=1).str[0].str[0] # Extract group from 'Echipa' column
    options_clean = df['Optiuni'].fillna('').str.replace(' ', '', regex=False) # Clean 'Optiuni' column by removing spaces and filling NaN values with empty strings
    domains_split = options_clean.str.split(',', expand=True).fillna('') # Split 'Optiuni' into multiple columns based on commas, filling NaN with empty strings
    df['d1'] = domains_split[0].str.split('-', n=1).str[0] # Extract first domain from the split columns
    df['d2'] = domains_split[1].str.split('-', n=1).str[0] # Extract second domain from the split columns
    df['d3'] = domains_split[2].str.split('-', n=1).str[0] # Extract third domain from the split columns
    df['domenii'] = options_clean.str.split(',') # Store the cleaned options as a list in a new column
    mask_d3_dup = (df['d3'] == df['d1']) | (df['d3'] == df['d2']) | (df['d3'] == '') # Create a mask for duplicate domains in 'd3'
    df.loc[mask_d3_dup, 'd3'] = '' # Set 'd3' to empty string if it is a duplicate of 'd1' or 'd2' or if it is empty
    mask_d2_dup = (df['d2'] == df['d1']) | (df['d2'] == '') # Create a mask for duplicate domains in 'd2'
    df.loc[mask_d2_dup, 'd2'] = df.loc[mask_d2_dup, 'd3'] # Set 'd2' to 'd3' if it is a duplicate of 'd1' or if it is empty
    df.loc[mask_d2_dup, 'd3'] = '' # Set 'd3' to empty string if 'd2' was set to 'd3'
    df[['alocare', 'runda', 'tema_proiect']] = '' # Initialize new columns for allocation, round, and project theme
    return df # Preprocessed DataFrame with new columns for group, domains, and cleaned options

def allocate_round(df: pandas.DataFrame, domain_col: str, round_num: int) -> tuple[pandas.DataFrame, int]:
    """
    Allocate projects for a specific round based on the given domain column.

    :param df: Input DataFrame containing team and domain information.
    :param domain_col: Column name for the domain to allocate (e.g., 'd1', 'd2', 'd3').
    :param round_num: The round number for allocation (1, 2, or 3).
    :return: Tuple containing the updated DataFrame and the number of allocations made.
    """
    
    mask = (df['alocare'] == '') & (df[domain_col] != '') # Create a mask for teams that have not been allocated and have a valid domain in the specified column
    if not mask.any(): # If no teams meet the criteria, return the DataFrame unchanged and zero allocations
        return df, 0 # If no candidates, return unchanged DataFrame and zero allocations
        
    candidates = df[mask] # Filter the DataFrame to get candidates that can be allocated
    allocated_dict = {} # Dictionary to keep track of already allocated domains for each group
    if (df['alocare'] != '').any(): # If there are already allocations, populate the allocated_dict
        for group, domains in df[df['alocare'] != ''].groupby('grupa')['alocare']: # Group by 'grupa' and collect already allocated domains
            allocated_dict[group] = set(domains) # Store allocated domains in a set for fast lookup
    
    rng = numpy.random.RandomState(SEED + round_num) # Create a random number generator with a seed based on the round number
    team_indices = [] # List to store indices of teams that will be allocated
    allocated_domains = [] # List to store allocated domains for the teams
    groups = candidates.groupby(['grupa', domain_col]) # Group candidates by 'grupa' and the specified domain column
    
    for (group, domain), group_df in groups: # Iterate over each group and domain combination
        if group in allocated_dict and domain in allocated_dict[group]: # If the group already has this domain allocated, skip it
            continue # Skip already allocated domains
        
        team_count = len(group_df) # Count the number of teams in the current group and domain
        if team_count == 1: # If there is only one team in the group, allocate it directly
            idx = group_df.index[0] # Get the index of the single team
        else:
            random_idx = rng.randint(0, team_count) # Generate a random index to select a team from the group
            idx = group_df.index[random_idx] # Get the index of the randomly selected team
        
        team_indices.append(idx) # Store the index of the team to be allocated
        allocated_domains.append(domain) # Store the allocated domain for the team
        
        if group in allocated_dict: # If the group already has allocated domains, add the new domain to the set
            allocated_dict[group].add(domain) # Otherwise, create a new set with the domain
        else:
            allocated_dict[group] = {domain} # Create a new set for the group with the allocated domain
    
    if team_indices:
        df.loc[team_indices, 'alocare'] = allocated_domains # Update the 'alocare' column for the allocated teams
        df.loc[team_indices, 'runda'] = str(round_num) # Update the 'runda' column for the allocated teams
        return df, len(team_indices) # Return the updated DataFrame and the number of allocations made
    
    return df, 0

def update_preferences(df: pandas.DataFrame, round_num: int) -> pandas.DataFrame:
    """
    Update the preferences of teams based on their allocations in previous rounds.

    :param df: Input DataFrame containing team and domain information.
    :param round_num: The round number for which to update preferences (2 or 3).
    :return: Updated DataFrame with modified preferences.
    """
    allocated_mask = df['alocare'] != '' # Create a mask for teams that have already been allocated a domain
    if not allocated_mask.any(): # If no teams have been allocated, return the DataFrame unchanged
        return df
    
    allocated_dict = {} # Dictionary to keep track of already allocated domains for each group
    for group, domains in df[allocated_mask].groupby('grupa')['alocare']: # Group by 'grupa' and collect already allocated domains
        allocated_dict[group] = set(domains) # Store allocated domains in a set for fast lookup
    
    if round_num == 2:
        d2_new = numpy.empty(len(df), dtype=object) # Initialize a new array for 'd2' preferences
        d3_new = numpy.empty(len(df), dtype=object) # Initialize a new array for 'd3' preferences
        
        grupas = df['grupa'].values # Get the 'grupa' values from the DataFrame
        d2s = df['d2'].values # Get the 'd2' values from the DataFrame
        d3s = df['d3'].values # Get the 'd3' values from the DataFrame
        
        for i in range(len(df)): # Iterate over each row in the DataFrame
            grupa = grupas[i] # Get the group for the current row
            d2 = d2s[i] # Get the 'd2' preference for the current row
            d3 = d3s[i] # Get the 'd3' preference for the current row
            
            if grupa not in allocated_dict: # If the group has no previous allocations
                d2_new[i] = d2 # Keep 'd2' as is
                d3_new[i] = d3 # Keep 'd3' as is
            elif d2 in allocated_dict[grupa]: # If 'd2' is already allocated in this group
                if d3 and d3 not in allocated_dict[grupa]: # If 'd3' is not allocated in this group
                    d2_new[i] = d3 # Move 'd3' to 'd2'
                    d3_new[i] = '' # Clear 'd3'
                else:
                    d2_new[i] = '' # Clear 'd2' if both 'd2' and 'd3' are allocated
                    d3_new[i] = '' # Clear 'd3' if both are allocated
            else:
                d2_new[i] = d2 # Keep 'd2' as is if it is not allocated
                d3_new[i] = d3 # Keep 'd3' as is if it is not allocated
        
        df['d2'] = d2_new # Update the 'd2' column with the new preferences
        df['d3'] = d3_new # Update the 'd3' column with the new preferences
        
    elif round_num == 3: # If this is the third round of allocation
        d3_new = numpy.empty(len(df), dtype=object) # Initialize a new array for 'd3' preferences
        grupas = df['grupa'].values # Get the 'grupa' values from the DataFrame
        d3s = df['d3'].values # Get the 'd3' values from the DataFrame
        
        for i in range(len(df)): # Iterate over each row in the DataFrame
            grupa = grupas[i] # Get the group for the current row
            d3 = d3s[i] # Get the 'd3' preference for the current row
            
            if grupa in allocated_dict and d3 in allocated_dict[grupa]: # If 'd3' is already allocated in this group
                d3_new[i] = '' # Clear 'd3' if it is already allocated
            else:
                d3_new[i] = d3 # Keep 'd3' as is if it is not allocated
                
        df['d3'] = d3_new # Update the 'd3' column with the new preferences
    
    return df # Update the DataFrame with modified preferences based on allocations in previous rounds

def assign_themes(df: pandas.DataFrame) -> pandas.DataFrame:
    """
    Assign project themes based on the allocated domains and preferences.

    :param df: Input DataFrame containing team and domain information.
    :return: Updated DataFrame with assigned project themes.
    """
    themes = numpy.empty(len(df), dtype=object) # Initialize an empty array for themes
    
    alocari = df['alocare'].values # Get the allocated domains from the DataFrame
    domeniii = df['domenii'].values # Get the domains from the DataFrame
    
    for i in range(len(df)): # Iterate over each row in the DataFrame
        alocare = alocari[i] # Get the allocated domain for the current row
        if not alocare: 
            themes[i] = 'De alocat manual' # If no allocation, set theme to 'De alocat manual'
            continue
        
        found = False # Flag to check if a theme is found
        for tema in domeniii[i]: # Iterate over the domains for the current row
            if tema and tema.startswith(alocare): # Check if the domain starts with the allocated domain
                themes[i] = tema # Assign the theme if found
                found = True # Set the flag to True if a theme is found
                break
                
        if not found:
            themes[i] = 'De alocat manual' # If no theme is found, set it to 'De alocat manual'
    
    df['tema_proiect'] = themes # Assign the themes to the DataFrame
    return df # Updated DataFrame with assigned project themes

def allocate_projects() -> pandas.DataFrame:
    """
    Main function to allocate projects based on team preferences and domains.

    :param None: No parameters required.
    :return: DataFrame with allocated projects and themes.
    """
    try: # Read the input CSV file and preprocess the data
        df = pandas.read_csv(INPUT_PATH,  
                encoding='utf-8',
                engine='c',
                low_memory=False,
                dtype={'Echipa': 'string', 'Optiuni': 'string'}) 
        # Ensure the 'Echipa' and 'Optiuni' columns are treated as strings
        # Df uses 'c' engine for better performance with large files
        # I used pyarrow and python engine, but it was slower than 'c' engine
        
        allocation_stats = {'round1': 0, 'round2': 0, 'round3': 0} # Dictionary to store allocation statistics for each round
        df = preprocess_dataframe(df) # Preprocess the DataFrame to extract groups and domains
        df, allocation_stats['round1'] = allocate_round(df, 'd1', 1) # Allocate projects for the first round
        df = update_preferences(df, 2) # Update preferences based on the first round allocations
        df, allocation_stats['round2'] = allocate_round(df, 'd2', 2) # Allocate projects for the second round
        df = update_preferences(df, 3) # Update preferences based on the second round allocations
        df, allocation_stats['round3'] = allocate_round(df, 'd3', 3) # Allocate projects for the third round
        df = assign_themes(df) # Assign project themes based on the allocated domains and preferences
        df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8') # Save the results to a CSV file
        return df # Return the DataFrame with allocated projects and themes
    except Exception as e: # Handle any exceptions that occur during the allocation process
        import sys # Import sys for error handling
        print(f"Error: {e}", file=sys.stderr) # Print the error message to standard error
        return None

def main() -> None:
    """
    Main function to set up the environment and run the project allocation.

    :return: None
    """
    pandas.set_option('display.expand_frame_repr', False) # Configure pandas to not wrap DataFrame output
    pandas.set_option('display.max_rows', 100) # Set maximum number of rows to display in DataFrame output
    
    allocate_projects() # Call the function to allocate projects and save the results

if __name__ == "__main__":
    main()

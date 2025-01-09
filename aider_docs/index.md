# Instructions on how to add indexing CLI

The file graphrag/cli/main.py includes CLI commands such as index, init and query. I'd like you to add another command new.
This command can accept various parameters:
--env, the path to the .env file that has the environment params.

## CLI interactive params

The new CLI new command should invoke an interactive shell that will ask the user for the following details:

1. Project Name
2. Index Name (each project is comprised of one or more indices, each one holds its own separate set of documents and indexing metadata)
3. Dataset Format (only 'rss' is supported for now)
4. RSS Feed URL
5. DOM element for scraping (default: <HTML> = entire DOM)
6. Number of max links to fetch (default 10) 
7. Domain name

## Flow of Actions

1. Project folder creation 

Based on the project name and index name, constuct a folder name: <project-name>-<index-name>
Check if that folder already exists and set IS_EXIST bool varaible accordingly.
If IS_EXISTS == False - create that folder, and create under it an input folder; otherwise, create just the input folder (or not at all, if input also exists)

2. Document fetching

Follow the RSS link a and fetch up to 'max links' links from there; follow each link, and scrape all text in the DOM that starts with "dom element" param.
Save each of these links as its own separate txt file, in the input folder.

3. Init project

Use initialize_project_at function at graphrag/cli/initialize.py to init project
As path param, provide the pass to the newly created folder (or existing one if IS_EXIST) <project-name>-<index-name>

4. Copy .env

If --env path was provided, copy the .env file at this part, to the root folder

5. Tune prompt

Use prompt_tune command at graphrag/cli/prompt_tune.py to invoke prompt tuning
For root, use the pass to the newly created folder (or existing one if IS_EXIST) <project-name>-<index-name>
For domain, use the cli provided domain param
For other params, use the defaults as in main.py, _prompt_tune_cli command

6. Indexing

Use index_cli command at graphrag/cli/index.py to invoke indexing
For root, use the pass to the newly created folder (or existing one if IS_EXIST) <project-name>-<index-name>
For other params, use the defaults as in main.py, _index_cli command

7. Loading into Neo4j DB

Use load_cli command at graphrag/cli/load.py to invoke loading into db
For root, use the pass to the newly created folder (or existing one if IS_EXIST) <project-name>-<index-name>
For other params, use the defaults as in main.py, _load_cli command

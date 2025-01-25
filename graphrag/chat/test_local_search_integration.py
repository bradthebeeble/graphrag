import pytest
from pathlib import Path
from graphrag.chat.prompt_templates import PROMPT_TEMPLATES, get_prompt_template
from graphrag.chat.util import parse_json_from_markdown
from graphrag.cli.query import run_local_search
from graphrag.config.load_config import load_config

def test_local_search_with_prompt_template():
    """Test integration between PROMPT_TEMPLATES and run_local_search"""
    # Get template tuple
    template_tuple = PROMPT_TEMPLATES["time-series"]
    query = get_prompt_template("time-series")
    # Format template with required variables
    response_type = template_tuple[1]
    
    # Create temporary test directory
    test_dir = Path("../awel-demo1")
    
    # Create minimal test config
    config_file = test_dir / "settings.yaml"
    
    # Run local search with test query
    (response, context_data) = run_local_search(
        config_filepath=config_file,
        data_dir=None,
        root_dir=test_dir,
        community_level=2,
        response_type=response_type,
        streaming=False,
        query=query
    )
    if isinstance(response, str):
        json_response = parse_json_from_markdown(response)
        if isinstance(json_response, list):
            print(json_response[0])


    
    # Verify response
    assert isinstance(response, str)
    assert len(response) > 0
    assert isinstance(context_data, dict)
    

if __name__ == "__main__":
    pytest.main(["-s", __file__])

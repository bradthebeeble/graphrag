###
## A set of pydantic definitions for music-related data
###

from typing import List, Optional
from pydantic import BaseModel, Field

# Pydantic
class Album(BaseModel):
    """A music album."""
    id: int = Field(description="Auto-generated uuid for the album")
    human_readable_id: int = Field(description="Human-readable id for the album. Echo it back from the input")
    title: str = Field(description="The title of the album")
    artist: str = Field(description="The name of the artist")
    year: int = Field(description="The year the album was released")
    release_date: Optional[int] = Field(
        default=None, description="The date the album was released"
    )
    genre: Optional[str] = Field(default=None, description="The genre of the album")
    label: Optional[str] = Field(default=None, description="The label of the album")

class ListOfAlbums(BaseModel):
    items: List[Album] = Field(description="A list of albums")

class Song(BaseModel):
    """A music song."""
    id: int = Field(description="Auto-generated uuid for the song")
    human_readable_id: int = Field(description="Human-readable id for the song. Echo it back from the input")
    title: str = Field(description="The title of the song")
    artist: str = Field(description="The name of the artist")
    album: Optional[str] = Field(default=None, description="The album the song belongs to")
    track_number: Optional[int] = Field(default=None, description="The track number on the album")
    duration: Optional[int] = Field(default=None, description="The duration of the song in seconds")
    genre: Optional[str] = Field(default=None, description="The genre of the song")
    year: Optional[int] = Field(default=None, description="The year the song was released")

class ListOfSongs(BaseModel):
    items: List[Song] = Field(description="A list of songs")

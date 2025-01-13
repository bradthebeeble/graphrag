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

class Artist(BaseModel):
    """A music artist."""
    id: int = Field(description="Auto-generated uuid for the artist")
    human_readable_id: int = Field(description="Human-readable id for the artist. Echo it back from the input")
    name: str = Field(description="The name of the artist")
    country: Optional[str] = Field(default=None, description="The country of origin")
    active_since: Optional[int] = Field(default=None, description="Year when the artist became active")
    genres: Optional[List[str]] = Field(default=None, description="List of genres associated with the artist")

class ListOfArtists(BaseModel):
    items: List[Artist] = Field(description="A list of artists")

class Label(BaseModel):
    """A music label."""
    id: int = Field(description="Auto-generated uuid for the label")
    human_readable_id: int = Field(description="Human-readable id for the label. Echo it back from the input")
    name: str = Field(description="The name of the label")
    founded: Optional[int] = Field(default=None, description="Year the label was founded")
    country: Optional[str] = Field(default=None, description="Country where the label is based")
    parent_company: Optional[str] = Field(default=None, description="Parent company of the label")

class ListOfLabels(BaseModel):
    items: List[Label] = Field(description="A list of labels")

class Performance(BaseModel):
    """A music performance."""
    id: int = Field(description="Auto-generated uuid for the performance")
    human_readable_id: int = Field(description="Human-readable id for the performance. Echo it back from the input")
    artist: str = Field(description="The performing artist")
    venue: str = Field(description="The venue of the performance")
    date: Optional[str] = Field(default=None, description="Date of the performance")
    setlist: Optional[List[str]] = Field(default=None, description="List of songs performed")

class ListOfPerformances(BaseModel):
    items: List[Performance] = Field(description="A list of performances")

class Genre(BaseModel):
    """A music genre."""
    id: int = Field(description="Auto-generated uuid for the genre")
    human_readable_id: int = Field(description="Human-readable id for the genre. Echo it back from the input")
    name: str = Field(description="The name of the genre")
    description: Optional[str] = Field(default=None, description="Description of the genre")
    parent_genre: Optional[str] = Field(default=None, description="Parent genre if this is a subgenre")
    era: Optional[str] = Field(default=None, description="The primary era of the genre")

class ListOfGenres(BaseModel):
    items: List[Genre] = Field(description="A list of genres")

from dataclasses import dataclass, asdict
from hashlib import sha256

TRACKS = ("br_internship", "global_entry", "global_freelance")

@dataclass
class Opportunity:
    title: str
    company: str
    url: str
    description: str
    location: str = ""
    track: str = "global_entry"
    source: str = "manual"
    remote: bool = False
    country_restrictions: str = ""
    budget: str = ""
    id: str = ""

    def __post_init__(self):
        if self.track not in TRACKS:
            raise ValueError("Trilha desconhecida")
        if not self.url.startswith(("https://", "http://")):
            raise ValueError("URL inválida")
        if not self.id:
            self.id = sha256(self.url.strip().lower().encode()).hexdigest()[:20]

    def asdict(self):
        return asdict(self)

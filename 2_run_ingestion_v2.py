import re
import os
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
import chromadb
from sentence_transformers import SentenceTransformer
import warnings

# Suppress a specific warning from sentence_transformers
warnings.filterwarnings("ignore", message="Default sentence-transformer model was used.*")

# region: Data Structures and Parser
@dataclass
class MonsterAbilityScores:
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

@dataclass
class MonsterAttack:
    name: str
    attack_bonus: int
    damage_dice: str
    damage_type: str
    range: Optional[str] = None
    description: Optional[str] = None

@dataclass
class MonsterCombatStats:
    armor_class: int
    hit_points: int
    hit_dice: str
    speed: Dict[str, str]
    ability_scores: MonsterAbilityScores
    saving_throws: Optional[Dict[str, int]] = None
    skills: Optional[Dict[str, int]] = None

@dataclass
class Monster:
    name: str
    size: str
    creature_type: str
    alignment: str
    challenge_rating: str
    combat_stats: MonsterCombatStats
    attacks: List[MonsterAttack]
    special_abilities: List[str]
    description: str
    environment: List[str]
    senses: Optional[str] = None
    languages: Optional[str] = None
    damage_resistances: Optional[List[str]] = None
    damage_immunities: Optional[List[str]] = None
    condition_immunities: Optional[List[str]] = None
    traits: Optional[List[str]] = None
    actions: Optional[List[str]] = None
    reactions: Optional[List[str]] = None
    legendary_actions: Optional[List[str]] = None

class ImprovedMonsterParser:
    def __init__(self):
        self.patterns = {
            'size_type_alignment': r'(Tiny|Small|Medium|Large|Huge|Gargantuan)\s+(aberration|beast|celestial|construct|dragon|elemental|fey|fiend|giant|humanoid|monstrosity|ooze|plant|undead)[, ]\s*(.+?)(?:\n|$)',
            'armor_class': r'Armor Class\s+(\d+)',
            'hit_points': r'Hit Points\s+(\d+)\s*\(([^)]+)\)',
            'speed': r'Speed\s+(.+?)(?=\nSTR|\n\n|\Z)',
            'ability_scores': r'STR\s+DEX\s+CON\s+INT\s+WIS\s+CHA\s*\n\s*(\d+)\s*\([+-]?\d+\)\s*(\d+)\s*\([+-]?\d+\)\s*(\d+)\s*\([+-]?\d+\)\s*(\d+)\s*\([+-]?\d+\)\s*(\d+)\s*\([+-]?\d+\)\s*(\d+)\s*\([+-]?\d+\)',
            'saving_throws': r'Saving Throws\s+([^\n]+)',
            'skills': r'Skills\s+([^\n]+)',
            'damage_resistances': r'Damage Resistances\s+([^\n]+)',
            'damage_immunities': r'Damage Immunities\s+([^\n]+)',
            'condition_immunities': r'Condition Immunities\s+([^\n]+)',
            'senses': r'Senses\s+([^\n]+)',
            'languages': r'Languages\s+([^\n]+)',
            'challenge': r'Challenge\s+([^(\s]+)'
        }

    def parse_monster_block(self, block_text: str) -> Optional[Monster]:
        monster_name_guess = block_text.split('\n')[0].strip()
        try:
            if len(block_text) < 50: return None
            lines = [line.strip() for line in block_text.split('\n') if line.strip()]
            name = self._extract_name(lines)
            if not name: return None

            size, creature_type, alignment = self._extract_size_type_alignment(block_text)
            if not size or not creature_type: return None

            combat_stats = MonsterCombatStats(
                armor_class=self._extract_generic_stat(block_text, 'armor_class', 10, int),
                hit_points=(self._extract_hit_points(block_text) or (10, '1d8'))[0],
                hit_dice=(self._extract_hit_points(block_text) or (10, '1d8'))[1],
                speed=self._extract_speed(block_text) or {'walk': '30 ft.'},
                ability_scores=self._extract_ability_scores(block_text) or MonsterAbilityScores(10,10,10,10,10,10),
                saving_throws=self._extract_saving_throws(block_text),
                skills=self._extract_skills(block_text)
            )

            return Monster(
                name=name, size=size, creature_type=creature_type, alignment=alignment or 'Unaligned',
                challenge_rating=self._extract_generic_stat(block_text, 'challenge', '0', str),
                combat_stats=combat_stats, attacks=[], special_abilities=[], description='', environment=[],
                senses=self._extract_generic_stat(block_text, 'senses', '', str),
                languages=self._extract_generic_stat(block_text, 'languages', '', str),
                damage_resistances=self._extract_list_stat(block_text, 'damage_resistances'),
                damage_immunities=self._extract_list_stat(block_text, 'damage_immunities'),
                condition_immunities=self._extract_list_stat(block_text, 'condition_immunities')
            )
        except Exception:
            return None

    def _extract_name(self, lines: List[str]) -> Optional[str]:
        if not lines: return None
        first_line = lines[0].strip()
        if first_line.isupper(): return first_line.title()
        return None

    def _extract_size_type_alignment(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        match = re.search(self.patterns['size_type_alignment'], text, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2), match.group(3).strip()
        return None, None, None

    def _extract_generic_stat(self, text: str, key: str, default: Any, type_converter: type) -> Any:
        match = re.search(self.patterns[key], text, re.IGNORECASE)
        if match:
            try: return type_converter(match.group(1).strip())
            except (ValueError, IndexError): return default
        return default

    def _extract_list_stat(self, text: str, key: str) -> Optional[List[str]]:
        match = re.search(self.patterns[key], text, re.IGNORECASE)
        if match:
            return [item.strip() for item in match.group(1).split(',')]
        return None

    def _extract_hit_points(self, text: str) -> Optional[Tuple[int, str]]:
        match = re.search(self.patterns['hit_points'], text, re.IGNORECASE)
        if match:
            try: return int(match.group(1)), match.group(2)
            except (ValueError, IndexError): return None
        return None

    def _extract_speed(self, text: str) -> Optional[Dict[str, str]]:
        match = re.search(self.patterns['speed'], text, re.IGNORECASE)
        if match:
            speed_text = match.group(1).strip()
            return {s.split(' ')[0]: s for s in speed_text.split(',')}
        return None

    def _extract_ability_scores(self, text: str) -> Optional[MonsterAbilityScores]:
        match = re.search(self.patterns['ability_scores'], text, re.DOTALL)
        if match:
            try:
                scores = [int(s) for s in match.groups()]
                return MonsterAbilityScores(*scores)
            except (ValueError, IndexError): return None
        return None

    def _extract_saving_throws(self, text: str) -> Optional[Dict[str, int]]:
        match = re.search(self.patterns['saving_throws'], text, re.IGNORECASE)
        if match:
            saves = {}
            try:
                for part in match.group(1).split(','):
                    ability, bonus = part.strip().split(' ')
                    saves[ability] = int(bonus)
                return saves
            except ValueError: return None
        return None

    def _extract_skills(self, text: str) -> Optional[Dict[str, int]]:
        match = re.search(self.patterns['skills'], text, re.IGNORECASE)
        if match:
            skills = {}
            try:
                for part in match.group(1).split(','):
                    name, bonus = part.strip().split(' ')
                    skills[name] = int(bonus)
                return skills
            except ValueError: return None
        return None
# endregion

# region: Chunking Logic
@dataclass
class MonsterChunk:
    monster_name: str
    content: str
    chunk_type: str
    metadata: Dict[str, Any]

    def get_retrieval_text(self) -> str:
        return f"Monster: {self.monster_name} ({self.chunk_type})\n{self.content}"

class MonsterChunkCreator:
    def create_monster_chunks(self, monster: Monster) -> List[MonsterChunk]:
        chunks = []
        base_metadata = self._create_base_metadata(monster)

        stats_content = f"Size: {monster.size} {monster.creature_type}\nAlignment: {monster.alignment}\nCR: {monster.challenge_rating}\nAC: {monster.combat_stats.armor_class}\nHP: {monster.combat_stats.hit_points} ({monster.combat_stats.hit_dice})\nSpeed: {monster.combat_stats.speed}"
        chunks.append(MonsterChunk(monster.name, stats_content, "stats", base_metadata))

        abilities_content = f"Abilities: STR {monster.combat_stats.ability_scores.strength}, DEX {monster.combat_stats.ability_scores.dexterity}, CON {monster.combat_stats.ability_scores.constitution}, INT {monster.combat_stats.ability_scores.intelligence}, WIS {monster.combat_stats.ability_scores.wisdom}, CHA {monster.combat_stats.ability_scores.charisma}"
        if monster.combat_stats.saving_throws: abilities_content += f"\nSaving Throws: {monster.combat_stats.saving_throws}"
        if monster.combat_stats.skills: abilities_content += f"\nSkills: {monster.combat_stats.skills}"
        chunks.append(MonsterChunk(monster.name, abilities_content, "abilities", base_metadata))

        defense_content = ''
        if monster.damage_resistances: defense_content += f"Resistances: {', '.join(monster.damage_resistances)}\n"
        if monster.damage_immunities: defense_content += f"Immunities: {', '.join(monster.damage_immunities)}\n"
        if monster.condition_immunities: defense_content += f"Condition Immunities: {', '.join(monster.condition_immunities)}\n"
        if monster.senses: defense_content += f"Senses: {monster.senses}"
        if defense_content:
            chunks.append(MonsterChunk(monster.name, defense_content.strip(), "defenses", base_metadata))

        return chunks

    def _create_base_metadata(self, monster: Monster) -> Dict[str, Any]:
        return {
            "monster_name": monster.name,
            "size": monster.size,
            "type": monster.creature_type,
            "alignment": monster.alignment,
            "cr": str(monster.challenge_rating)
        }
# endregion

# region: ChromaDB Management
class MonsterChromaManagerV2:
    def __init__(self, db_path: str = "./chromadb", collection_name: str = "dnd_monsters_v2"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"ChromaDB Manager (V2) on collection '{self.collection_name}' initialized.")

    def add_monster_chunks(self, chunks: List[MonsterChunk]):
        if not chunks: return
        ids = [f"{chunk.monster_name}-{chunk.chunk_type}-{i}".replace(' ', '_') for i, chunk in enumerate(chunks)]
        documents = [chunk.get_retrieval_text() for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        # Filter out metadata values that are not supported by ChromaDB
        for meta in metadatas:
            for key, value in meta.items():
                if not isinstance(value, (str, int, float, bool)):
                    meta[key] = str(value)

        embeddings = self.embedding_model.encode(documents).tolist()
        self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)

    def clear_collection(self):
        print(f"Clearing collection: {self.collection_name}")
        try:
            self.client.delete_collection(name=self.collection_name)
        except ValueError:
            print(f"Collection '{self.collection_name}' did not exist, skipping deletion.")
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        print("Collection created.")
# endregion

# region: The Pipeline
class MonsterFilesToChromaPipeline:
    def __init__(self, db_path: str = "./chromadb"):
        self.parser = ImprovedMonsterParser()
        self.chunk_creator = MonsterChunkCreator()
        self.chroma_manager = MonsterChromaManagerV2(db_path)

    def process_monster_files(self, monster_dir: str, clear_existing: bool = False):
        print("Starting Monster Files to ChromaDB pipeline...")
        if clear_existing:
            self.chroma_manager.clear_collection()

        if not os.path.isdir(monster_dir):
            print(f"Error: Directory '{monster_dir}' not found.")
            return

        monster_files = [f for f in os.listdir(monster_dir) if f.endswith('.txt')]
        print(f"Found {len(monster_files)} monster files in '{monster_dir}'.")

        successful_parses = 0
        failed_parses = 0
        total_chunks_added = 0

        for i, filename in enumerate(monster_files):
            filepath = os.path.join(monster_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                block_text = f.read()
            
            monster = self.parser.parse_monster_block(block_text)
            if monster:
                chunks = self.chunk_creator.create_monster_chunks(monster)
                self.chroma_manager.add_monster_chunks(chunks)
                total_chunks_added += len(chunks)
                successful_parses += 1
                print(f"PARSING_SUCCESS: {filename}")
            else:
                failed_parses += 1
                print(f"PARSING_FAILURE: {filename}")
            
            if (i + 1) % 50 == 0:
                print(f"Processed {i+1}/{len(monster_files)} files... ({successful_parses} successes, {total_chunks_added} chunks)")

        print(f"\nPipeline Complete!")
        print(f"  Successfully parsed and loaded: {successful_parses} monsters")
        print(f"  Failed to parse: {failed_parses} files")
        print(f"  Total chunks added to '{self.chroma_manager.collection_name}': {total_chunks_added}")
# endregion

# region: Run the Pipeline
if __name__ == "__main__":
    pipeline = MonsterFilesToChromaPipeline()
    pipeline.process_monster_files('data/monsters_raw/', clear_existing=True)

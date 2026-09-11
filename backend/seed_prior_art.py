import os
import json
from uuid import uuid4
from datetime import datetime, timezone

# Add backend directory to sys path so we can import from app
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from app.db import SessionLocal
from app.models import Source, SourceVersion, Chunk, CorpusRelease
from app.retrieval import encoder

def uid():
    return str(uuid4())

def now():
    return datetime.now(timezone.utc)

PLANTS = [
    {
        'name': 'Ashwagandha',
        'synonyms': ['Withania somnifera', 'winter cherry', 'Indian ginseng'],
        'description': 'Ashwagandha (Withania somnifera) is an adaptogenic herb used in traditional medicine. Known for its root extract which is rich in withanolides.',
        'tkdl': 'TKDL/AY/ASH-001: Rasayana use documented in Charaka Samhita. TKDL/AY/ASH-002: Ashwagandha Churna for stress-relief.'
    },
    {
        'name': 'Turmeric',
        'synonyms': ['Curcuma longa', 'haldi', 'curcumin', 'haridra'],
        'description': 'Turmeric (Curcuma longa) is widely used for its anti-inflammatory and antioxidant properties, primarily attributed to curcuminoids.',
        'tkdl': 'TKDL/AY/TUR-001: Haridra wound healing in Sushruta Samhita. TKDL/AY/TUR-002: Haridra Khanda for skin disorders.'
    },
    {
        'name': 'Neem',
        'synonyms': ['Azadirachta indica', 'nimba', 'margosa', 'neem leaf'],
        'description': 'Neem (Azadirachta indica) is a tree known for its bitter properties and antibacterial, antifungal, and insecticidal applications (azadirachtin).',
        'tkdl': 'TKDL/AY/NIM-001: Krimighna properties in Charaka Samhita. EP patent on neem fungicidal use revoked using TKDL.'
    },
    {
        'name': 'Tulsi',
        'synonyms': ['Ocimum tenuiflorum', 'Ocimum sanctum', 'holy basil', 'tulasi'],
        'description': 'Tulsi (Ocimum sanctum) or Holy Basil is an aromatic shrub used for immunomodulatory, adaptogenic, and respiratory treatments.',
        'tkdl': 'TKDL/AY/TUL-001: Shwasahara and Kasahara use in Bhavaprakasha Nighantu.'
    },
    {
        'name': 'Giloy',
        'synonyms': ['Tinospora cordifolia', 'guduchi', 'amrita'],
        'description': 'Giloy (Tinospora cordifolia) is a climbing shrub with immunomodulatory and antipyretic (Jwarahara) properties.',
        'tkdl': 'TKDL/AY/GUD-001: Rasayana and Jwarahara use documented in Charaka Samhita and Ashtanga Hridaya.'
    },
    {
        'name': 'Shatavari',
        'synonyms': ['Asparagus racemosus', 'satavar', 'wild asparagus'],
        'description': 'Shatavari (Asparagus racemosus) is known as a female reproductive tonic, galactagogue, and adaptogen containing steroidal saponins.',
        'tkdl': 'TKDL/AY/SHA-001: Stanya-janana and Balya use documented in Dhanvantari Nighantu.'
    },
    {
        'name': 'Brahmi',
        'synonyms': ['Bacopa monnieri', 'water hyssop', 'gotu kola', 'Centella asiatica'],
        'description': 'Brahmi refers to cognitive-enhancing (Medhya Rasayana) herbs like Bacopa monnieri, standardized for bacoside content.',
        'tkdl': 'TKDL/AY/BRA-001: Medhya Rasayana use in Charaka Samhita. TKDL/AY/BRA-002: Brahmi Ghrita in Ashtanga Hridaya.'
    },
    {
        'name': 'Triphala',
        'synonyms': ['amalaki', 'haritaki', 'bibhitaki', 'three fruits'],
        'description': 'Triphala is a classical Tridoshahara formulation consisting of three fruits (Amalaki, Haritaki, Bibhitaki) used for digestion and antioxidant support.',
        'tkdl': 'TKDL/AY/TRI-001: Triphala classical Tridoshahara formulation in Charaka Samhita and Sushruta Samhita.'
    },
    {
        'name': 'Guggulu',
        'synonyms': ['Commiphora wightii', 'guggul', 'mukul myrrh'],
        'description': 'Guggulu (Commiphora wightii) produces a resin extract used for lipid-lowering (Medohara) and anti-arthritic applications (guggulsterones).',
        'tkdl': 'TKDL/AY/GUG-001: Medohara properties in Sushruta Samhita. TKDL/AY/GUG-002: Yograj Guggulu anti-inflammatory formulation.'
    },
    {
        'name': 'Amla',
        'synonyms': ['Phyllanthus emblica', 'Emblica officinalis', 'amalaki', 'Indian gooseberry'],
        'description': 'Amla (Phyllanthus emblica) is a rich source of vitamin C and tannins, used extensively as a Rasayana and Vayasthapana (anti-ageing) ingredient.',
        'tkdl': 'TKDL/AY/AML-001: Rasayana use in Charaka Samhita. TKDL/AY/AML-002: Primary ingredient in Chyawanprash.'
    }
]

def seed():
    print("Loading embedding model...")
    model = encoder()
    if not model:
        print("Error: Embedding model could not be loaded. Make sure embeddings are enabled.")
        return

    with SessionLocal() as db:
        # Get or create an active corpus release
        release = db.query(CorpusRelease).filter_by(active=True).first()
        if not release:
            release = CorpusRelease(id=uid(), name='Pilot Data', version_ids=[], active=True, created_at=now())
            db.add(release)
            db.flush()

        new_version_ids = []

        for plant in PLANTS:
            print(f"Seeding {plant['name']}...")
            
            source_id = uid()
            source = Source(
                id=source_id,
                title=f"{plant['name']} Prior Art Database",
                publisher="TKDL Mock Dataset",
                url=f"https://www.tkdl.res.in/mock/{plant['name'].lower()}",
                jurisdiction="india",
                market="treaties",  # Treaties market to align with default prior-art search
                category="prior_art",
                authority="guidance",
                language="en",
                disposition="approved",
                checked_at=now(),
                access="public"
            )
            
            version_id = uid()
            version = SourceVersion(
                id=version_id,
                source_id=source_id,
                checksum=str(hash(plant['description'] + plant['tkdl'])),
                path=f"mock/{plant['name'].lower()}.txt",
                retrieved_at=now(),
                review_status='approved'
            )
            
            # Create text to embed
            full_text = f"Name: {plant['name']}\nSynonyms: {', '.join(plant['synonyms'])}\nDescription: {plant['description']}\nTKDL References: {plant['tkdl']}"
            
            db.add(source)
            db.add(version)
            db.flush()
            
            # Embed with passage: prefix for e5 models
            embedding = model.encode([f"passage: {full_text}"], normalize_embeddings=True)[0].tolist()
            
            chunk = Chunk(
                id=uid(),
                version_id=version_id,
                ordinal=1,
                heading=f"{plant['name']} Overview",
                text=full_text,
                embedding=embedding
            )
            
            db.add(chunk)
            
            new_version_ids.append(version_id)

        # Update the active release with the new version IDs
        updated_versions = list(release.version_ids) + new_version_ids
        release.version_ids = updated_versions
        
        db.commit()
        print(f"Successfully seeded 10 plants and updated corpus release {release.id}")

if __name__ == "__main__":
    seed()

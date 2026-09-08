"""
Comprehensive Language + Knowledge Training
Builds: Markov vocabulary, Word trees, Knowledge trees, Function words, Hilbert embeddings
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, '.')
from quantum_language_engine import QuantumLanguageEngine
from quantum_markov_quantum import QuantumMarkovEngine

def train_markov_vocabulary(engine, oxford_file):
    """Initialize Markov with Oxford dictionary vocabulary"""
    print("📚 Training Markov vocabulary from Oxford dictionaries...")
    try:
        with open(oxford_file, 'r') as f:
            words = [line.strip().lower() for line in f if line.strip()]
        
        # Add to Markov chain
        for i in range(len(words)-2):
            prefix = (words[i], words[i+1])
            next_word = words[i+2]
            if prefix not in engine.markov.chain:
                engine.markov.chain[prefix] = {}
            engine.markov.chain[prefix][next_word] = engine.markov.chain[prefix].get(next_word, 0) + 1
        
        print(f"✓ Markov vocabulary: {len(words)} words, {len(engine.markov.chain)} states")
        return True
    except Exception as e:
        print(f"✗ Markov training failed: {e}")
        return False

def build_word_trees(engine, oxford_file):
    """Build word relationship trees from corpus"""
    print("🌳 Building word relationship trees...")
    try:
        with open(oxford_file, 'r') as f:
            words = [line.strip().lower() for line in f if line.strip()]
        
        word_graph = defaultdict(set)
        for i in range(len(words)-1):
            word_graph[words[i]].add(words[i+1])
            if i > 0:
                word_graph[words[i]].add(words[i-1])
        
        tree_file = Path(oxford_file).parent / 'word_tree.json'
        with open(tree_file, 'w') as f:
            json.dump({k: list(v) for k, v in word_graph.items()}, f)
        
        print(f"✓ Word tree: {len(word_graph)} words with relationships")
        return word_graph
    except Exception as e:
        print(f"✗ Word tree building failed: {e}")
        return None

def build_knowledge_tree(engine):
    """Build concept relationship tree from engine"""
    print("🌳 Building knowledge relationship tree...")
    try:
        concept_graph = defaultdict(set)
        
        if hasattr(engine, 'concepts'):
            for concept, data in engine.concepts.items():
                if isinstance(data, dict) and 'relationships' in data:
                    rels = data['relationships']
                    if isinstance(rels, dict):
                        concept_graph[concept].update(rels.keys())
                    elif isinstance(rels, list):
                        concept_graph[concept].update(rels)
        
        tree_file = Path.home() / '.quantum-mcagi' / 'knowledge_tree.json'
        with open(tree_file, 'w') as f:
            json.dump({k: list(v) for k, v in concept_graph.items()}, f)
        
        print(f"✓ Knowledge tree: {len(concept_graph)} concepts with relationships")
        return concept_graph
    except Exception as e:
        print(f"✗ Knowledge tree building failed: {e}")
        return None


def train_pennylane_circuits(engine):
    """Initialize PennyLane quantum circuits and Hilbert embeddings"""
    print("⚛️  Training PennyLane quantum circuits...")
    try:
        if hasattr(engine, 'hilbert_engine') and engine.hilbert_engine:
            # Initialize quantum state
            print("  • Initializing quantum state vectors...")
            engine.hilbert_engine.initialize_quantum_state()
            
            # Build semantic embeddings
            print("  • Building Hilbert semantic embeddings...")
            engine.hilbert_engine.train_embeddings(dim=128)
            
            print("✓ PennyLane quantum layer initialized")
            return True
        else:
            print("⚠ Hilbert engine not available")
            return False
    except Exception as e:
        print(f"✗ PennyLane training failed: {e}")
        return False


def main():
    print("=" * 60)
    print("COMPREHENSIVE LANGUAGE + KNOWLEDGE TRAINING")
    print("=" * 60)
    
    engine = QuantumLanguageEngine()
    oxford_file = '../Quantum_Brain_L/oxford_words.txt'
    
    # Train all components
    train_pennylane_circuits(engine)
    train_markov_vocabulary(engine, oxford_file)
    build_word_trees(engine, oxford_file)
    build_knowledge_tree(engine)
    
    # Save engine state
    engine.save_state(str(Path.home() / '.quantum-mcagi'))
    print("\n✓ Training complete. Engine state saved.")

if __name__ == '__main__':
    main()

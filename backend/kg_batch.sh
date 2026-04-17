#!/bin/bash
ENTITIES=(
  "Asia" "Australia" "Ancient Rome" "Ancient Greece" "Ancient Egypt"
  "Middle Ages" "Renaissance" "World War I" "Cold War"
  "Human brain" "DNA" "Evolution" "Cell biology" "Immune system"
  "Psychology" "Memory" "Language" "Mathematics" "Physics"
  "Chemistry" "Ecology" "Climate" "Ocean" "Solar System"
  "Galaxy" "Big Bang" "Economics" "Democracy" "Philosophy"
  "Ethics" "Religion" "Islam" "Christianity" "Buddhism"
  "Hinduism" "Music" "Art" "Literature" "Medicine"
  "Computer science" "Internet" "Artificial intelligence" "Law"
  "Sociology" "Anthropology" "Archaeology" "Mythology"
  "Thermodynamics" "Relativity" "Water" "Energy" "War"
  "Rome" "Italy" "Greece" "Japan" "China" "India" "Russia"
  "United States" "France" "Germany" "Brazil"
  "Quantum mechanics" "Dark matter" "Consciousness" "Free will"
  "Neuroscience" "Cosmology" "Black hole" "String theory"
  "Natural selection" "Genetics" "Climate change"
  "Renewable energy" "Biodiversity" "Colonialism" "Feminism"
  "Human rights" "Globalization" "Inflation" "Game theory"
  "Information theory" "Cryptography" "Machine learning"
  "Poetry" "Philosophy of mind" "Epistemology" "Metaphysics"
  "Plato" "Aristotle" "Kant" "Nietzsche" "Einstein" "Newton"
  "Darwin" "Shakespeare" "Buddha" "Jesus" "Muhammad"
  "Roman Empire" "Ottoman Empire" "British Empire" "Silk Road"
  "Sleep" "Dream" "Emotion" "Mental health" "Depression"
  "Vaccine" "Antibiotic" "Robot" "Blockchain" "Constitution"
)

for entity in "${ENTITIES[@]}"; do
  echo "Ingesting: $entity"
  python3 ~/Quantum_MCAGI_NO_LLM/backend/wikidata_ingester.py "$entity"
  sleep 5
done

echo "Done"

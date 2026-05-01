"""
Question Generation Utilities for NoteGenie
"""
import re
import random
from typing import List, Dict, Tuple
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag

class QuestionGenerator:
    """Generate exam-oriented questions from study material"""
    
    def __init__(self):
        # Question templates
        self.templates = {
            'definition': [
                "What is the definition of {term}?",
                "Define {term}.",
                "Explain what is meant by {term}."
            ],
            'concept': [
                "Explain the concept of {concept}.",
                "What is {concept} and how does it work?",
                "Describe the key aspects of {concept}."
            ],
            'difference': [
                "What is the difference between {term1} and {term2}?",
                "Compare and contrast {term1} with {term2}.",
                "How does {term1} differ from {term2}?"
            ],
            'advantage': [
                "What are the advantages of {concept}?",
                "List the benefits of using {concept}.",
                "Why is {concept} advantageous?"
            ],
            'disadvantage': [
                "What are the disadvantages of {concept}?",
                "List the limitations of {concept}.",
                "What are the drawbacks of {concept}?"
            ],
            'application': [
                "What are the applications of {concept}?",
                "How is {concept} used in practice?",
                "Give examples of where {concept} is applied."
            ],
            'mcq': [
                "Which of the following best describes {term}?",
                "What is the primary purpose of {concept}?",
                "Which statement about {term} is correct?"
            ]
        }
    
    def extract_key_terms(self, text: str, max_terms: int = 10) -> List[str]:
        """Extract key terms from text using simple heuristics"""
        # Clean text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Get words
        words = word_tokenize(text)
        
        # Remove stopwords (simple list)
        stopwords = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                        'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were',
                        'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
                        'did', 'will', 'would', 'should', 'can', 'could', 'may',
                        'might', 'must', 'shall'])
        
        # Filter and count
        word_counts = {}
        for word in words:
            if word not in stopwords and len(word) > 2:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get most frequent terms
        sorted_terms = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [term for term, _ in sorted_terms[:max_terms]]
    
    def extract_concepts(self, text: str) -> List[str]:
        """Extract concepts and definitions from text"""
        concepts = []
        sentences = sent_tokenize(text)
        
        for sentence in sentences:
            # Look for patterns like "X is Y", "X refers to Y", "X means Y"
            patterns = [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*) is (?:a|an|the)?\s*([^,.]+)',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*) refers to ([^,.]+)',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*) means ([^,.]+)',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*) can be defined as ([^,.]+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    if match[0] and match[1]:
                        concepts.append({
                            'term': match[0].strip(),
                            'definition': match[1].strip()
                        })
        
        return concepts
    
    def generate_definition_questions(self, concepts: List[Dict]) -> List[Dict]:
        """Generate definition-based questions"""
        questions = []
        
        for concept in concepts:
            term = concept['term']
            template = random.choice(self.templates['definition'])
            question = template.format(term=term)
            
            questions.append({
                'type': 'definition',
                'question': question,
                'answer': concept['definition'],
                'term': term
            })
        
        return questions
    
    def generate_comparison_questions(self, terms: List[str]) -> List[Dict]:
        """Generate comparison questions"""
        questions = []
        
        if len(terms) >= 2:
            for i in range(min(len(terms), 5)):
                for j in range(i + 1, min(len(terms), 5)):
                    if i != j:
                        template = random.choice(self.templates['difference'])
                        question = template.format(term1=terms[i], term2=terms[j])
                        
                        questions.append({
                            'type': 'comparison',
                            'question': question,
                            'terms': [terms[i], terms[j]],
                            'answer': f"Compare {terms[i]} and {terms[j]} based on their characteristics, functions, and applications."
                        })
        
        return questions
    
    def generate_mcq_questions(self, text: str, num_questions: int = 5) -> List[Dict]:
        """Generate multiple choice questions"""
        questions = []
        sentences = sent_tokenize(text)
        
        if len(sentences) < 3:
            return questions
        
        for _ in range(min(num_questions, len(sentences))):
            # Pick a sentence and create a cloze question
            sentence = random.choice(sentences)
            
            # Replace a noun with blank
            words = word_tokenize(sentence)
            tagged = pos_tag(words)
            
            # Find nouns
            nouns = [word for word, tag in tagged if tag.startswith('NN')]
            
            if nouns:
                target = random.choice(nouns)
                question_text = sentence.replace(target, "______")
                
                # Create distractors
                other_nouns = [n for n in nouns if n != target]
                distractors = random.sample(other_nouns, min(3, len(other_nouns)))
                
                # Ensure we have 4 options
                options = [target] + distractors
                while len(options) < 4:
                    options.append(f"Option {len(options) + 1}")
                
                random.shuffle(options)
                correct_index = options.index(target)
                
                questions.append({
                    'type': 'mcq',
                    'question': f"Fill in the blank: {question_text}",
                    'options': options,
                    'correct_answer': target,
                    'correct_index': correct_index,
                    'explanation': f"The correct term is '{target}' which fits grammatically and contextually in the sentence."
                })
        
        return questions
    
    def generate_questions(self, text: str, question_types: List[str] = None, num_questions: int = 10) -> Dict:
        """Generate various types of questions from text"""
        
        if question_types is None:
            question_types = ['definition', 'comparison', 'mcq']
        
        all_questions = []
        
        # Extract information from text
        key_terms = self.extract_key_terms(text)
        concepts = self.extract_concepts(text)
        
        # Generate questions by type
        if 'definition' in question_types and concepts:
            all_questions.extend(self.generate_definition_questions(concepts))
        
        if 'comparison' in question_types and len(key_terms) >= 2:
            all_questions.extend(self.generate_comparison_questions(key_terms))
        
        if 'mcq' in question_types:
            all_questions.extend(self.generate_mcq_questions(text, num_questions=3))
        
        # If we don't have enough questions, generate generic ones
        if len(all_questions) < num_questions:
            sentences = sent_tokenize(text)
            for i in range(min(len(sentences), num_questions - len(all_questions))):
                sentence = sentences[i]
                if len(sentence.split()) > 5:  # Avoid very short sentences
                    all_questions.append({
                        'type': 'comprehension',
                        'question': f"Explain: {sentence}",
                        'answer': f"This statement discusses: {sentence}",
                        'source': f"Sentence {i+1} from the text"
                    })
        
        # Limit to requested number
        all_questions = all_questions[:num_questions]
        
        return {
            'total_questions': len(all_questions),
            'questions': all_questions,
            'text_stats': {
                'sentences': len(sent_tokenize(text)),
                'words': len(word_tokenize(text)),
                'characters': len(text),
                'key_terms_found': len(key_terms),
                'concepts_found': len(concepts)
            }
        }
    
    def format_questions_for_display(self, questions_data: Dict) -> str:
        """Format questions in a readable way"""
        questions = questions_data['questions']
        stats = questions_data['text_stats']
        
        output = f"📚 Generated {questions_data['total_questions']} Questions\n"
        output += f"Based on text with {stats['sentences']} sentences, {stats['words']} words\n"
        output += f"Found {stats['key_terms_found']} key terms and {stats['concepts_found']} concepts\n"
        output += "=" * 60 + "\n\n"
        
        for i, q in enumerate(questions, 1):
            output += f"{i}. [{q['type'].upper()}] {q['question']}\n"
            
            if q['type'] == 'mcq':
                for j, option in enumerate(q['options']):
                    letter = chr(65 + j)  # A, B, C, D
                    output += f"   {letter}. {option}\n"
                output += f"   ✅ Answer: {q['options'][q['correct_index']]} (Option {chr(65 + q['correct_index'])})\n"
            else:
                output += f"   💡 Answer: {q.get('answer', 'N/A')}\n"
            
            if 'explanation' in q:
                output += f"   📝 Explanation: {q['explanation']}\n"
            
            output += "\n"
        
        return output
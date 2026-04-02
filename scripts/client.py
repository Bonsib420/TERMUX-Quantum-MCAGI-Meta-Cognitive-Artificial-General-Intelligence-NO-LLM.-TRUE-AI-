#!/usr/bin/env python
"""
Quantum MCAGI v2.0 - Python Client
Interactive chat client for the Quantum AI
"""

import requests
import json
import sys
import os

SERVER_URL = "http://localhost:5000"

def print_color(text, color=None):
    colors = {
        'green': '\033[92m',
        'cyan': '\033[96m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'magenta': '\033[95m',
        'reset': '\033[0m'
    }
    if color and color in colors:
        print(f"{colors[color]}{text}{colors['reset']}")
    else:
        print(text)

def handle_command(user_input, conv_id):
    if user_input.startswith('/research '):
        parts = user_input.split(' ')
        depth = 10
        topic_parts = []
        for p in parts[1:]:
            if p.startswith('-') and p[1:].isdigit():
                depth = int(p[1:])
            else:
                topic_parts.append(p)
        topic = ' '.join(topic_parts)
        payload = {
            'text': f"Give me {depth} detailed research points about: {topic}. Format as numbered list.",
            'conversation_id': conv_id
        }
        response = requests.post(f"{SERVER_URL}/api/chat", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print_color(f"\n🔬 Research: {topic}", 'cyan')
                print_color(data['data']['response'], 'green')
        print()
        return True
    return False

def main():
    print_color("=" * 60, 'cyan')
    print_color("QUANTUM MCAGI v2.0 - Interactive Client", 'cyan')
    print_color("=" * 60, 'cyan')

    try:
        response = requests.get(f"{SERVER_URL}/api/status")
        if response.status_code == 200:
            status = response.json()
            print_color(f"\n✅ Connected to Quantum AI", 'green')
            print_color(f"   Stage: {status['growth_stage']['name']}", 'green')
        else:
            print_color(f"\n❌ Server error: {response.status_code}", 'red')
            return
    except requests.exceptions.ConnectionError:
        print_color(f"\n❌ Cannot connect to server at {SERVER_URL}", 'red')
        return

    try:
        response = requests.post(f"{SERVER_URL}/api/conversation/start")
        conv_id = response.json()['conversation_id']
        print_color(f"\n📝 Conversation ID: {conv_id}", 'yellow')
    except Exception as e:
        print_color(f"❌ Error starting conversation: {e}", 'red')
        return

    print_color("\n" + "=" * 60, 'cyan')
    print_color("Commands: /research <topic> -<depth>", 'yellow')
    print_color("=" * 60 + "\n", 'cyan')

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            if not user_input.strip():
                continue
            if handle_command(user_input, conv_id):
                continue

            payload = {'text': user_input, 'conversation_id': conv_id}
            response = requests.post(f"{SERVER_URL}/api/chat", json=payload)

            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    result = data['data']
                    print_color(f"\n🤖 AI: {result['response']}", 'green')
                    if result.get('concepts'):
                        concepts = [c['concept'] for c in result['concepts']]
                        print_color(f"   📊 Concepts: {', '.join(concepts)}", 'yellow')
                    if result.get('explanation'):
                        print_color(f"   💭 {result['explanation']['summary']}", 'cyan')
                    if result.get('growth_stage'):
                        stage = result['growth_stage']
                        print_color(f"   📈 Stage: {stage['name']} ({stage['progress']:.0%})", 'magenta')
                    print()
        except KeyboardInterrupt:
            print_color("\n\n👋 Goodbye!", 'yellow')
            break
        except Exception as e:
            print_color(f"❌ Error: {e}", 'red')

if __name__ == '__main__':
    main()

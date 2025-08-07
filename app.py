#!/usr/bin/env python3
"""
Web-based Video Transcript Search Tool
Run with: python app.py
Access at: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify
import json
import os
import glob
import re
from datetime import timedelta

app = Flask(__name__)

class TranscriptSearcher:
    def __init__(self, transcript_dir="transcripts"):
        self.transcript_dir = transcript_dir
        self.transcripts = self.load_transcripts()
    
    def load_transcripts(self):
        """Load all JSON transcript files"""
        transcripts = {}
        pattern = os.path.join(self.transcript_dir, "*.json")
        
        for json_file in glob.glob(pattern):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    video_name = os.path.splitext(os.path.basename(json_file))[0]
                    transcripts[video_name] = data
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        return transcripts
    
    def format_timestamp(self, seconds):
        """Convert seconds to MM:SS format"""
        return str(timedelta(seconds=int(seconds)))
    
    def search(self, query, case_sensitive=False):
        """Search for query across all transcripts"""
        results = []
        
        if not case_sensitive:
            query = query.lower()
        
        for video_name, transcript in self.transcripts.items():
            if 'segments' in transcript:
                for segment in transcript['segments']:
                    text = segment.get('text', '')
                    if not case_sensitive:
                        text = text.lower()
                    
                    if query in text:
                        results.append({
                            'video': video_name,
                            'timestamp': self.format_timestamp(segment['start']),
                            'start_seconds': segment['start'],
                            'end_seconds': segment['end'],
                            'text': segment.get('text', '').strip(),
                            'youtube_url': f"https://youtube.com/watch?v={self.extract_video_id(video_name)}&t={int(segment['start'])}s"
                        })
        
        return sorted(results, key=lambda x: (x['video'], x['start_seconds']))
    
    def extract_video_id(self, video_name):
        """Extract YouTube video ID from filename"""
        match = re.search(r'\[([a-zA-Z0-9_-]{11})\]', video_name)
        return match.group(1) if match else ""

# Initialize searcher
searcher = TranscriptSearcher()

@app.route('/')
def index():
    total_videos = len(searcher.transcripts)
    return render_template('index.html', total_videos=total_videos)

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '').strip()
    if not query:
        return jsonify({'results': [], 'error': 'Please enter a search query'})
    
    try:
        results = searcher.search(query)
        return jsonify({
            'results': results[:50],  # Limit to 50 results
            'total_found': len(results),
            'query': query
        })
    except Exception as e:
        return jsonify({'results': [], 'error': str(e)})

@app.route('/videos')
def list_videos():
    """List all available videos"""
    videos = list(searcher.transcripts.keys())
    return jsonify({'videos': videos})

if __name__ == '__main__':
    if not searcher.transcripts:
        print("No transcripts found! Make sure JSON files are in 'transcripts' directory.")
    else:
        print(f"Loaded {len(searcher.transcripts)} video transcripts")
        print("Starting web server at http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
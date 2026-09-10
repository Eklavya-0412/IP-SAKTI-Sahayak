"""Create a local deployment configuration without printing secrets."""
import argparse,secrets
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--output',default='.env');args=parser.parse_args()
target=(ROOT/args.output).resolve()
if not target.is_relative_to(ROOT):raise ValueError('Configuration must stay in the project directory.')
if target.exists():raise SystemExit('Configuration exists; edit it explicitly instead of overwriting secrets.')
password=secrets.token_urlsafe(32)
text=(ROOT/'.env.example').read_text().replace('change-this-password',password).replace('replace-with-at-least-32-random-characters',secrets.token_urlsafe(48))
if args.output!='.env':text='ENV_FILE='+args.output+'\n'+text
target.write_text(text,encoding='utf-8');print('Created configuration. Keep it private; never commit it.')

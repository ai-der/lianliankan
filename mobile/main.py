# main.py
import asyncio
from LinkGame import LinkGame

if __name__ == "__main__":
    try:
        asyncio.run(LinkGame().run())
    except KeyboardInterrupt:
        pass
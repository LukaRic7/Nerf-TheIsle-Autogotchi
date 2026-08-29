from datetime import datetime
import os, requests, time
import loggerric as lr

# ============================================= #
#  CONSTANTS & GLOBALS
# ============================================= #

COOKIE = os.getenv('COOKIE', '')
if not COOKIE:
    lr.Log.warn("COOKIE environment variable is empty or not set!")
    exit(1)

# ============================================= #
#  FETCHING
# ============================================= #

def fetch_pet() -> dict:
    """
    **Fetch a players pet data.**
    
    *Returns*:
    - (dict): The pet data.
    """

    response = requests.get('https://api.nerfofficial.org/api/dinogame/pet',
                            headers={ 'Cookie': COOKIE })
    if not response.ok:
        lr.Log.error(f'[{response.status_code}] {response.reason}')

    data:dict = response.json()
    if not data.get('success', False):
        lr.Log.warn(f'Data dit not succeed: {data.get('message', 'NO MESSAGE')}')

    return data.get('pet', {})

def post_action(action:str) -> dict:
    """
    **Send a POST request with the specified action.**
    
    *Parameters*:
    - `action` (str): The action path to POST.
    
    *Returns*:
    - (dict): The response data JSON parsed.
    """

    response = requests.post(f'https://api.nerfofficial.org/api/dinogame/{action}',
                             headers={ 'Cookie': COOKIE })

    if not response.ok and response.status_code != 400:
        lr.Log.error(f'[{response.status_code}] {response.reason}')

    return response.json()

def claim_daily() -> dict:
    """
    **Claim the daily reward.**
    
    *Returns*:
    - (dict): The response data JSON parsed.
    """

    response = requests.post('https://api.nerfofficial.org/api/dinogame/daily-reward',
                            headers={ 'Cookie': COOKIE })
    if not response.ok and response.status_code != 400:
        lr.Log.error(f'[{response.status_code}] {response.reason}')

    return response.json()

# ============================================= #
#  MAIN
# ============================================= #

def main():
    """
    **Main entrypoint.**
    """

    while True:
        pet = fetch_pet()

        name    = pet.get('name', 'NO NAME')
        level   = pet.get('level', 0)
        xp      = pet.get('experience', 0)
        xp_next = pet.get('experienceToNext', 0)
        lr.Log.info(f'Name: {name} | Level {level} [{xp}/{xp_next} XP]', highlight=name)
        lr.Log.info(f'Hunger: {pet.get('hunger', 0):.1f}%', align_key=11)
        lr.Log.info(f'Happiness: {pet.get('happiness', 0):.1f}%', align_key=11)
        lr.Log.info(f'Cleanliness: {pet.get('cleanliness', 0):.1f}%', align_key=11)
        lr.Log.info(f'Energy: {pet.get('energy', 0):.1f}%', align_key=11)

        if pet.get('isSleeping', False):
            sleep_until:str = pet.get('sleepUntil', '')
            target          = datetime.fromisoformat(sleep_until.replace('Z', '+00:00'))
            delta           = target.astimezone() - datetime.now().astimezone()

            total_minutes  = max(0, int(delta.total_seconds() // 60))
            hours, minutes = divmod(total_minutes, 60)

            time_formatted = f'{hours}h {minutes}m'
            lr.Log.info(f'Sleeping, wakes up in {time_formatted}', highlight=time_formatted)

        last_claim:str = pet.get('lastDailyReward', '')
        target         = datetime.fromisoformat(last_claim.replace('Z', '+00:00'))
        delta          = target.astimezone() - datetime.now().astimezone()

        total_minutes  = max(0, 1440 + int(delta.total_seconds() // 60))
        hours, minutes = divmod(total_minutes, 60)

        print('')

        if total_minutes == 0:
            reward = claim_daily()

            lr.Log.info(f'Bones Rewarded: {reward.get('bonesReward', 0)}', align_key=14)
            lr.Log.info(f'New Balance: {reward.get('newBalance', 0)}', align_key=14)
            lr.Log.info(f'XP Rewarded: {reward.get('xpReward', 0)}', align_key=14)
            
            level   = pet.get('level', 0)
            xp      = pet.get('experience', 0)
            xp_next = pet.get('experienceToNext', 0)
            lr.Log.info(f'Level {level} [{xp}/{xp_next} XP]')
        else:
            time_formatted = f'{hours}h {minutes}m'
            lr.Log.info(f'Claim reward in: {time_formatted}', highlight=time_formatted)

        cooldowns:dict[str, int] = pet.get('cooldowns', {})
        for action, cooldown in cooldowns.items():
            if isinstance(cooldown, int):
                lr.Log.info(f'{action.title()} is on cooldown, try again in: {cooldown}m',
                            highlight=[action.title(), f'{cooldown}m'])
            else:
                reward = post_action(action)
                del reward['success']

                if action == 'sleep':
                    sleeping_for:int = reward.get('sleepMinutes', 0)
                    lr.Log.info(f'Sleeping for: {sleeping_for} minutes',
                                highlight=str(sleeping_for))
                else:
                    new_value = reward.get(list(reward.keys())[0])
                    lr.Log.info(f'New {action.title()} is {new_value:.2f}%',
                                highlight=[action.title(), f'{new_value:.2f}%'])

        time.sleep(60*60)

if __name__ == '__main__': main()
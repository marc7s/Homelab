#!/usr/bin/python

class FilterModule(object):
    def filters(self):
        return {'get_remote_env_filename': self.get_remote_env_filename}

    def get_remote_env_filename(self, env_filename, env_name):
        remote_env_filename = env_filename.replace(".vault", "")
        
        # Handle Angular environment files
        if 'environment' in remote_env_filename:
            remote_env_filename = f'src/environments/{remote_env_filename}'
        # Handle normal .env files
        else:
            remote_env_filename = remote_env_filename.replace(f'.{env_name}', '')
        
        return remote_env_filename
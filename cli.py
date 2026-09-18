import sys
from infrastructure_cli_utils import get_cli_app, CliSettings
from infrastructure_builder import BuildParameters
from infrastructure_path_utils import get_root_dir_path
from config import settings

root_dir = get_root_dir_path()

# конфигурация сборки bin/exe
build_settings = BuildParameters(
    name=settings.app_name,
    one_file=True,
    entry_point_path=root_dir / 'main.py',
    copy_from_dist_to_target_dir=root_dir,
    create_resources_symlink=False,
    delete_releases_folder=True,
    no_show_process=False,
)

app = get_cli_app(
    exe_mode=getattr(sys, 'frozen', False),
    name=settings.app_name,
    root_dir=get_root_dir_path(),
    cli_settings=CliSettings(enable_build_command=True, enable_git_push=True),
    build_settings=build_settings,
)

if __name__ == '__main__':
    app()

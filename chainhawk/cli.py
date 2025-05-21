import click
from .adapters.semgrep_adapter import run_semgrep

@click.command()
@click.option('--target', '-t', required=True, help='분석할 스마트 컨트랙트 경로')
@click.option('--rules', '-r', default='semgrep_rules', help='Semgrep 룰셋 디렉터리 또는 config')
@click.option('--debug', '-d', is_flag=True, help='디버그 모드 활성화')
def main(target, rules, debug):
    """Semgrep을 통한 스마트 컨트랙트 정적 분석 실행"""
    if debug:
        click.echo("[디버그] 분석 시작...")
        click.echo(f"[디버그] 대상 파일: {target}")
        click.echo(f"[디버그] 룰셋 경로: {rules}")
    
    results = run_semgrep(target, rules, debug)
    click.echo("[분석 결과]")
    click.echo(results)

if __name__ == '__main__':
    main() 
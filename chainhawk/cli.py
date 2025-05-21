import click
from .adapters.semgrep_adapter import run_semgrep

@click.command()
@click.option('--target', '-t', required=True, help='분석할 스마트 컨트랙트 경로')
def main(target):
    """Semgrep을 통한 스마트 컨트랙트 정적 분석 실행"""
    results = run_semgrep(target)
    click.echo("[분석 결과]")
    click.echo(results)

if __name__ == '__main__':
    main() 
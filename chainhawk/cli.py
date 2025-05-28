import click
from .adapters.semgrep_adapter import run_semgrep
from .adapters.ityfuzz_adapter import run_ityfuzz

@click.group()
def cli():
    """Chainhawk - 스마트 컨트랙트 분석 도구"""
    pass

@click.command()
@click.option('--target', '-t', required=True, help='분석할 스마트 컨트랙트 경로')
@click.option('--rules', '-r', default='semgrep_rules', help='Semgrep 룰셋 디렉터리 또는 config')
@click.option('--engine', '-e', default='semgrep', type=click.Choice(['semgrep', 'ityfuzz']), show_default=True, help='분석 엔진 선택')
@click.option('--debug', '-d', is_flag=True, help='디버그 모드 활성화')
def analyze(target, rules, engine, debug):
    """스마트 컨트랙트 취약점 분석 실행 (Semgrep/ITYfuzz)"""
    if debug:
        click.echo(f"[디버그] 분석 시작... (엔진: {engine})")
        click.echo(f"[디버그] 대상 파일: {target}")
        if engine == 'semgrep':
            click.echo(f"[디버그] 룰셋 경로: {rules}")

    if engine == 'semgrep':
        results = run_semgrep(target, rules, debug)
    elif engine == 'ityfuzz':
        results = run_ityfuzz(target, debug)
    else:
        results = '[오류] 지원하지 않는 분석 엔진입니다.'
    
    click.echo("[분석 결과]")
    click.echo(results)

@click.command()
def validate():
    """도구 설정 검증"""
    click.echo("🔧 Chainhawk 설정 검증 중...")
    
    # Docker 확인
    import subprocess
    try:
        docker_result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if docker_result.returncode == 0:
            click.echo("✅ Docker: 사용 가능")
        else:
            click.echo("❌ Docker: 사용 불가")
    except FileNotFoundError:
        click.echo("❌ Docker: 설치되지 않음")
    
    # Foundry 확인 (ITYfuzz용)
    try:
        forge_result = subprocess.run(['forge', '--version'], capture_output=True, text=True)
        if forge_result.returncode == 0:
            click.echo("✅ Foundry (forge): 사용 가능")
        else:
            click.echo("❌ Foundry (forge): 사용 불가")
    except FileNotFoundError:
        click.echo("❌ Foundry: 설치되지 않음 (ITYfuzz 사용 시 필요)")
    
    # Semgrep 확인
    try:
        semgrep_result = subprocess.run(['semgrep', '--version'], capture_output=True, text=True)
        if semgrep_result.returncode == 0:
            click.echo("✅ Semgrep: 사용 가능")
        else:
            click.echo("❌ Semgrep: 사용 불가")
    except FileNotFoundError:
        click.echo("❌ Semgrep: 설치되지 않음")
    
    # curl 확인 (Anvil 상태 체크용)
    try:
        curl_result = subprocess.run(['curl', '--version'], capture_output=True, text=True)
        if curl_result.returncode == 0:
            click.echo("✅ curl: 사용 가능")
        else:
            click.echo("❌ curl: 사용 불가")
    except FileNotFoundError:
        click.echo("❌ curl: 설치되지 않음")
    
    click.echo("\n💡 ITYfuzz 사용 시 필요한 것들:")
    click.echo("  - Docker 이미지 빌드: docker build -f docker/ityfuzz.Dockerfile -t chainhawk-ityfuzz .")
    click.echo("  - Foundry 설치: curl -L https://foundry.paradigm.xyz | bash")

@click.command()
def info():
    """도구 정보 표시"""
    click.echo("🔧 Chainhawk - 스마트 컨트랙트 분석 도구")
    click.echo("="*50)
    click.echo("\n📋 지원하는 분석 엔진:")
    click.echo("  • semgrep  - 정적 분석 (SAST)")
    click.echo("  • ityfuzz  - 퍼징 분석 (동적 테스트)")
    click.echo("\n📖 사용 예시:")
    click.echo("  chainhawk analyze --target contract.sol --engine semgrep")
    click.echo("  chainhawk analyze --target contract.sol --engine ityfuzz --debug")
    click.echo("  chainhawk validate")

# 명령어 등록
cli.add_command(analyze)
cli.add_command(validate) 
cli.add_command(info)

# 기존 호환성을 위한 main 함수
@click.command()
@click.option('--target', '-t', required=True, help='분석할 스마트 컨트랙트 경로')
@click.option('--rules', '-r', default='semgrep_rules', help='Semgrep 룰셋 디렉터리 또는 config')
@click.option('--engine', '-e', default='semgrep', type=click.Choice(['semgrep', 'ityfuzz']), show_default=True, help='분석 엔진 선택')
@click.option('--debug', '-d', is_flag=True, help='디버그 모드 활성화')
def main(target, rules, engine, debug):
    """스마트 컨트랙트 취약점 분석 실행 (Semgrep/ITYfuzz)"""
    if debug:
        click.echo(f"[디버그] 분석 시작... (엔진: {engine})")
        click.echo(f"[디버그] 대상 파일: {target}")
        if engine == 'semgrep':
            click.echo(f"[디버그] 룰셋 경로: {rules}")

    if engine == 'semgrep':
        results = run_semgrep(target, rules, debug)
    elif engine == 'ityfuzz':
        results = run_ityfuzz(target, debug)
    else:
        results = '[오류] 지원하지 않는 분석 엔진입니다.'
    click.echo("[분석 결과]")
    click.echo(results)

if __name__ == '__main__':
    cli()